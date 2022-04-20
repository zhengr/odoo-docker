# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import requests
from urllib.parse import quote
from werkzeug.urls import url_join

from odoo import models, fields, _
from odoo.exceptions import UserError


class SocialLivePostLinkedin(models.Model):
    _inherit = 'social.live.post'

    linkedin_post_id = fields.Char('Actual LinkedIn ID of the post')

    def _refresh_statistics(self):
        super(SocialLivePostLinkedin, self)._refresh_statistics()
        accounts = self.env['social.account'].search([('media_type', '=', 'linkedin')])

        for account in accounts:
            linkedin_post_ids = self.env['social.live.post'].sudo().search([('account_id', '=', account.id)], order='create_date DESC', limit=700)
            if not linkedin_post_ids:
                continue

            linkedin_post_ids = {post.linkedin_post_id: post for post in linkedin_post_ids}

            endpoint = url_join(
                self.env['social.media']._LINKEDIN_ENDPOINT,
                'organizationalEntityShareStatistics?shares=List(%s)' % ','.join([quote(urn) for urn in linkedin_post_ids]))

            response = requests.get(
                endpoint, params={'q': 'organizationalEntity', 'organizationalEntity': account.linkedin_account_urn, 'count': 700},
                headers=account._linkedin_bearer_headers())

            if response.status_code != 200 or 'elements' not in response.json():
                account.sudo().write({'is_media_disconnected': True})
                continue

            for stats in response.json()['elements']:
                urn = stats.get('share')
                stats = stats.get('totalShareStatistics')

                if not urn or not stats or urn not in linkedin_post_ids:
                    continue

                linkedin_post_ids[urn].write({
                    'engagement': stats.get('likeCount', 0) + stats.get('commentCount', 0) + stats.get('shareCount', 0)
                })

    def _post(self):
        linkedin_live_posts = self.filtered(lambda post: post.account_id.media_type == 'linkedin')
        super(SocialLivePostLinkedin, (self - linkedin_live_posts))._post()

        linkedin_live_posts._post_linkedin()

    def _post_linkedin(self):
        for live_post in self:
            message_with_shortened_urls = self.env['mail.render.mixin'].sudo()._shorten_links_text(live_post.post_id.message, live_post._get_utm_values())

            url_in_message = self.env['social.post']._extract_url_from_message(message_with_shortened_urls)

            if live_post.post_id.image_ids:
                images_urn = [
                    self._linkedin_upload_image(live_post.account_id, image_id)
                    for image_id in live_post.post_id.image_ids
                ]

                specific_content = {
                    'com.linkedin.ugc.ShareContent': {
                        "shareCommentary": {
                            "text": message_with_shortened_urls
                        },
                        'shareMediaCategory': 'IMAGE',
                        'media': [{
                            "status": "READY",
                            "media": image_urn
                        } for image_urn in images_urn]
                    }
                }

            elif url_in_message:
                specific_content = {
                    'com.linkedin.ugc.ShareContent': {
                        "shareCommentary": {
                            "text": message_with_shortened_urls
                        },
                        'shareMediaCategory': 'ARTICLE',
                        'media': [{
                            "status": "READY",
                            "originalUrl": url_in_message
                        }]
                    }
                }

            else:
                specific_content = {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": message_with_shortened_urls
                        },
                        "shareMediaCategory": "NONE"
                    }
                }

            data = {
                "author": live_post.account_id.linkedin_account_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": specific_content,
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }

            response = requests.post(
                url_join(self.env['social.media']._LINKEDIN_ENDPOINT, 'ugcPosts'),
                headers=live_post.account_id._linkedin_bearer_headers(),
                json=data).json()

            response_id = response.get('id')
            values = {
                'state': 'posted' if response_id else 'failed',
                'failure_reason': False
            }
            if response_id:
                values['linkedin_post_id'] = response_id
            else:
                values['failure_reason'] = response.get('message', 'unknown')

            if response.get('serviceErrorCode') == 65600:
                # Invalid access token
                self.account_id.write({'is_media_disconnected': True})

            live_post.write(values)

    def _linkedin_upload_image(self, account_id, image_id):
        # 1 - Register your image to be uploaded
        data = {
            "registerUploadRequest": {
                "recipes": [
                    "urn:li:digitalmediaRecipe:feedshare-image"
                ],
                "owner": account_id.linkedin_account_urn,
                "serviceRelationships": [
                    {
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent"
                    }
                ]
            }
        }

        response = requests.post(
                url_join(self.env['social.media']._LINKEDIN_ENDPOINT, 'assets?action=registerUpload'),
                headers=account_id._linkedin_bearer_headers(),
                json=data).json()

        if 'value' not in response or 'asset' not in response['value']:
            raise UserError(_('Failed during upload registering'))

        # 2 - Upload image binary file
        upload_url = response['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
        image_urn = response['value']['asset']

        file = open(image_id._full_path(image_id.store_fname), 'rb').read()

        headers = account_id._linkedin_bearer_headers()
        headers['Content-Type'] = 'application/octet-stream'

        response = requests.request('POST', upload_url, data=file, headers=headers)

        if response.status_code != 201:
            raise UserError(_('Failed during image upload'))

        return image_urn
