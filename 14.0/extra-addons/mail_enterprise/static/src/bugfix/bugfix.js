/**
 * This file allows introducing new JS modules without contaminating other files.
 * This is useful when bug fixing requires adding such JS modules in stable
 * versions of Odoo. Any module that is defined in this file should be isolated
 * in its own file in master.
 */
odoo.define('mail_enterprise/static/src/bugfix/bugfix.js', function (require) {
'use strict';

const ChatterContainer = require('mail/static/src/components/chatter_container/chatter_container.js');
const { attr } = require('mail/static/src/model/model_field.js');
const { registerFieldPatchModel } = require('mail/static/src/model/model_core.js');

/**
 * This should be moved inside the mail_enterprise
 * mail_enterprise/static/src/models/chatter/chatter.js
 */
registerFieldPatchModel('mail.chatter', 'mail/static/src/models/chatter/chatter.js', {
    /**
     * The chatter is inside .form_sheet_bg class
     */
    isInFormSheetBg: attr({
        default: false,
    }),
});

/**
* mail_enterprise/static/src/models/chatter/chatter.js
*/
Object.assign(ChatterContainer, {
    defaultProps: Object.assign(ChatterContainer.defaultProps || {}, {
        isInFormSheetBg: false,
    }),
    props: Object.assign(ChatterContainer.props, {
        isInFormSheetBg: {
            type: Boolean,
        },
    })
});

});
