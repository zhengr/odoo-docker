odoo.define('documents.DocumentsListView', function (require) {
"use strict";

const DocumentsListController = require('documents.DocumentsListController');
const DocumentsListModel = require('documents.DocumentsListModel');
const DocumentsListRenderer = require('documents.DocumentsListRenderer');
const DocumentsSearchPanel = require('documents.DocumentsSearchPanel');
const DocumentsView = require('documents.viewMixin');

const ListView = require('web.ListView');
const viewRegistry = require('web.view_registry');

const DocumentsListView = ListView.extend(DocumentsView, {
    config: Object.assign({}, ListView.prototype.config, {
        Controller: DocumentsListController,
        Model: DocumentsListModel,
        Renderer: DocumentsListRenderer,
        SearchPanel: DocumentsSearchPanel,
    }),
});

viewRegistry.add('documents_list', DocumentsListView);

return DocumentsListView;

});
