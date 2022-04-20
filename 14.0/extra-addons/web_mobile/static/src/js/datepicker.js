odoo.define("web_mobile.datepicker", function (require) {
    "use strict";

    const mobile = require("web_mobile.core");

    if (!mobile.methods.requestDateTimePicker) {
        return;
    }

    const web_datepicker = require("web.datepicker");
    const Widget = require("web.Widget");

    /**
     * Override odoo date-picker (bootstrap date-picker) to display mobile native
     * date picker. Because of it is better to show native mobile date-picker to
     * improve usability of Application (Due to Mobile users are used to native
     * date picker).
     */

    web_datepicker.DateWidget.include({
        /**
         * @override
         */
        start() {
            this.$input = this.$("input.o_datepicker_input");
            this._setupMobilePicker();
        },

        /**
         * Bootstrap date-picker already destroyed at initialization
         *
         * @override
         */
        destroy: Widget.prototype.destroy,

        /**
         * @override
         */
        maxDate() {
            console.warn("Unsupported in the mobile applications");
        },

        /**
         * @override
         */
        minDate() {
            console.warn("Unsupported in the mobile applications");
        },

        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------

        /**
         * @override
         * @private
         */
        _setLibInputValue() {},

        /**
         * @private
         */
        _setupMobilePicker() {
            this.$el.on("click", async () => {
                const { data } = await mobile.methods.requestDateTimePicker({
                    value: this.getValue() ? this.getValue().format("YYYY-MM-DD HH:mm:ss") : false,
                    type: this.type_of_date,
                    ignore_timezone: true,
                });
                this.$input.val(data);
                this.changeDatetime();
            });
        },
    });
});
