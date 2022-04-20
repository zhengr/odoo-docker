odoo.define('hr_payroll.WorkEntryPayrollControllerMixin', function (require) {
    'use strict';

    var core = require('web.core');
    var time = require('web.time');

    var _t = core._t;
    var QWeb = core.qweb;

    var WorkEntryPayrollControllerMixin = {
        /**
         * @override
         * @returns {Promise}
         */
        _update: function () {
            var self = this;
            self._renderWorkEntryButtons();
            return this._super.apply(this, arguments);
        },

        /*
            Private
        */

        _renderWorkEntryButtons: function () {
            if (this.modelName !== "hr.work.entry") {
                return;
            }

            var records = this._fetchRecords();
            var hasConflicts = records.some(function (record) { return record.state === 'conflict'; });
            var allValidated = records.every(function (record) { return record.state === 'validated'; });

            this.$buttons.find('.btn-work-entry').remove();

            if (!allValidated && records.length !== 0) {
                this.$buttons.append(QWeb.render('hr_work_entry.work_entry_button', {
                    button_text: _t("Generate Payslips"),
                    event_class: 'btn-payslip-generate',
                    disabled: hasConflicts,
                }));
                this.$buttons.find('.btn-payslip-generate').on('click', this._onGeneratePayslips.bind(this));

            }
        },

        _generatePayslips: function () {
            this.do_action('hr_payroll.action_generate_payslips_from_work_entries', {
                additional_context: {
                    default_date_start: time.date_to_str(this.firstDay),
                    default_date_end: time.date_to_str(this.lastDay),
                },
            });
        },

        _onGeneratePayslips: function (e) {
            e.preventDefault();
            e.stopImmediatePropagation();
            this._generatePayslips();
        },
    };

    return WorkEntryPayrollControllerMixin;

});
