odoo.define("documents_spreadsheet.test_utils", function (require) {
    "use strict";
    const testUtils = require("web.test_utils");
    const PivotView = require("web.PivotView");

    const { createActionManager, nextTick, createView } = testUtils;

    function mockRPCFn(route, args) {
        if (args.method === "search_read" && args.model === "ir.model") {
            return Promise.resolve([{ name: "partner" }]);
        }
        return this._super.apply(this, arguments);
    }

    async function createSpreadsheetFromPivot(pivotView) {
        const { data, debug } = pivotView;
        const pivot = await createView(
            Object.assign({ View: PivotView }, pivotView)
        );
        const documents = data["documents.document"].records;
        const id = Math.max(...documents.map((d) => d.id)) + 1;
        documents.push({
            id,
            name: "pivot spreadsheet",
            raw: await pivot._getSpreadsheetData(),
        });
        pivot.destroy();
        const actionManager = await createActionManager({
            debug,
            data,
            mockRPC: pivotView.mockRPC || mockRPCFn,
            intercepts: pivotView.intercepts || {},
            services: pivotView.services || {},
            archs: pivotView.archs || {},
        });
        await actionManager.doAction({
            type: "ir.actions.client",
            tag: "action_open_spreadsheet",
            params: {
                active_id: id,
            },
        });
        await nextTick();
        const spreadSheetComponent = actionManager.getCurrentController().widget
            .spreadsheetComponent.componentRef.comp;
        const oSpreadsheetComponent = spreadSheetComponent.spreadsheet.comp
        const model = oSpreadsheetComponent.model;
        const env = Object.assign(spreadSheetComponent.env, {
            getters: model.getters,
            dispatch: model.dispatch,
            services: model.config.evalContext.env.services,
            openSidePanel: oSpreadsheetComponent.openSidePanel.bind(oSpreadsheetComponent),
        });
        return [actionManager, model, env];
    }

    return {
        createSpreadsheetFromPivot,
        mockRPCFn,
    };
});
