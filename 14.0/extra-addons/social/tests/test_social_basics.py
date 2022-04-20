# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.addons.social.tests import common


class TestSocialBasics(common.SocialCase):
    def test_social_post_create_multi(self):
        """ Ensure that a 'multi' creation of 2 social.posts also
        creates 2 associated utm.sources. """
        social_posts = self.env['social.post'].create([{
            'account_ids': [(4, self.social_account.id)],
            'message': 'Message 1'
        }, {
            'account_ids': [(4, self.social_account.id)],
            'message': 'Message 2'
        }])

        self.assertEqual(2, len(social_posts))
        self.assertEqual(2, len(social_posts.utm_source_id))
        self.assertNotEqual(social_posts[0].utm_source_id, social_posts[1].utm_source_id)

    @classmethod
    def _get_social_media(cls):
        return cls.env['social.media'].create({
            'name': 'Social Media',
        })
