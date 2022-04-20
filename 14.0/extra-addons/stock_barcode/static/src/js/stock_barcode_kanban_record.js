odoo.define('stock_barcode.InventoryAdjustmentKanbanRecord', function (require) {
"use strict";

var KanbanRecord = require('web.KanbanRecord');

var StockBarcodeKanbanRecord = KanbanRecord.extend({
    /**
     * @override
     * @private
     */
    _openRecord: function () {
        if (this.modelName === 'stock.inventory' && this.$el.parents('.o_stock_barcode_kanban').length) {
            this.do_action({
                type: 'ir.actions.client',
                tag: 'stock_barcode_inventory_client_action',
                params: {
                    'model': 'stock.inventory',
                    'inventory_id': this.id,
                }
            });
        } else {
            this._super.apply(this, arguments);
        }
    }
});

return StockBarcodeKanbanRecord;

});

odoo.define('stock_barcode.InventoryAdjustmentKanbanController', function (require) {
"use strict";
var KanbanController = require('web.KanbanController');

var StockBarcodeKanbanController = KanbanController.extend({
    // --------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Do not add a record but open new barcode views.
     *
     * @private
     * @override
     */
    _onButtonNew: function (ev) {
        if (this.modelName === 'stock.inventory') {
            this._rpc({
                model: 'stock.inventory',
                method: 'open_new_inventory',
            })
            .then((result) => {
                this.do_action(result);
            });
        } else if (this.modelName === 'stock.picking') {
            this._rpc({
                model: 'stock.picking',
                method: 'open_new_picking',
                context: this.initialState.context,
            }).then((result) => {
                this.do_action(result.action);
            });
        } else {
            this._super(...arguments);
        }
    },
});
return StockBarcodeKanbanController;

});
