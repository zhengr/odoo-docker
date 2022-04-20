odoo.define('social_linkedin.social_stream_post_kanban_controller', function (require) {
"use strict";

var StreamPostKanbanController = require('social.social_stream_post_kanban_controller');
var StreamPostLinkedInComments = require('social_linkedin.social_linkedin_post_kanban_comments');

StreamPostKanbanController.include({
    events: _.extend({}, StreamPostKanbanController.prototype.events, {
        'click .o_social_linkedin_comments': '_onLinkedInCommentsClick',
    }),

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    _onLinkedInCommentsClick: function (ev) {
        var self = this;
        var $target = $(ev.currentTarget);

        var postId = $target.data('postId');

        this._rpc({
            model: 'social.stream.post',
            method: 'get_linkedin_comments',
            args: [[postId]]
        }).then(function (result) {
            new StreamPostLinkedInComments(
                self,
                {
                    postId: postId,
                    accountId: result.accountId,
                    postAuthorImage: result.postAuthorImage,
                    currentUserUrn: result.currentUserUrn,
                    originalPost: $target.data(),
                    comments: result.comments,
                    summary: result.summary,
                    offset: result.offset
                }
            ).open();
        });
    },
});

return StreamPostKanbanController;

});
