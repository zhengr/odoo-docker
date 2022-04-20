odoo.define('stock_barcode.ListKanbanView', function (require) {
"use strict";

var StockBarcodeKanbanController = require('stock_barcode.InventoryAdjustmentKanbanController');
var StockBarcodeKanbanRenderer = require('stock_barcode.InventoryAdjustmentKanbanRenderer');

var KanbanView = require('web.KanbanView');
var view_registry = require('web.view_registry');

var StockBarcodeListKanbanView = KanbanView.extend({
	config: _.extend({}, KanbanView.prototype.config, {
		Controller: StockBarcodeKanbanController,
		Renderer: StockBarcodeKanbanRenderer,
	}),
});

view_registry.add('stock_barcode_list_kanban', StockBarcodeListKanbanView);

return StockBarcodeListKanbanView;

});
