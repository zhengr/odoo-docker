odoo.define('social.post_formatter_mixin', function (require) {
"use strict";

var SocialEmojisMixin = require('mail.emoji_mixin');

return {
    /**
     * Add emojis support
     * Wraps links, #hashtag and @tag around anchors
     * Regex from: https://stackoverflow.com/questions/19484370/how-do-i-automatically-wrap-text-urls-in-anchor-tags
     *
     * @param {String} formattedValue
     * @private
     */
    _formatPost: function (formattedValue) {
        // add emojis support and escape HTML
        formattedValue = SocialEmojisMixin._formatText(formattedValue);

        // highlight URLs
        formattedValue = formattedValue.replace(
            /http(s)?:\/\/(www\.)?[a-zA-Z0-9@:%_+~#=~#?&//=\-\.]{3,256}/g,
            "<a href='$&' target='_blank' rel='noreferrer noopener'>$&</a>");

        return formattedValue;
    },

    _getMediaType: function () {
        if (this.mediaType) {
            return this.mediaType;
        } else if (this.attrs && this.attrs.media_type) {
            return this.attrs.media_type;
        }
    },
};

});
