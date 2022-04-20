odoo.define('timesheet_grid.GridModel', function (require) {
    "use strict";

    const { _t } = require('web.core');
    const GridModel = require('web_grid.GridModel');

    const TimesheetGridModel = GridModel.extend({
        /**
         * @override
         */
        async reload(handle, params) {
            if (params && 'groupBy' in params) {
                // With timesheet grid, it makes nonsense to manage group_by with a field date (as the dates are already in the rows).
                // Detection of groupby date with ':' (date:day). Ignore grouped by date, and display warning.
                var GroupBy = params.groupBy.filter(filter => {
                    return filter.split(':').length === 1;
                });
                if (GroupBy.length !== params.groupBy.length) {
                    this.do_warn(false, _t('Grouping by date is not supported'));
                }
                params.groupBy = GroupBy;
            }
            return this._super(...arguments);
        },
    });

    return TimesheetGridModel;
});
