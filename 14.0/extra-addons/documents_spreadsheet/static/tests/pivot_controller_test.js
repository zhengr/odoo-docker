odoo.define("documents_spreadsheet.pivot_controller_test", function (require) {
    "use strict";

    const PivotView = require("web.PivotView");
    const testUtils = require("web.test_utils");
    const spreadsheet = require("documents_spreadsheet.spreadsheet_extended");
    const spreadsheetUtils = require("documents_spreadsheet.test_utils");
    const pivotUtils = require("documents_spreadsheet.pivot_utils");
    const CancelledReason = require('documents_spreadsheet.CancelledReason');
    const { Model } = spreadsheet;
    const toCartesian = spreadsheet.helpers.toCartesian;
    const { createSpreadsheetFromPivot, mockRPCFn } = spreadsheetUtils;
    const cellMenuRegistry = spreadsheet.registries.cellMenuRegistry;

    const createView = testUtils.createView;

    function getAutofillValue(model, from, column, increment) {
        const content = model.getters.getCell(...toCartesian(from)).content;
        return model.getters.getNextValue(content, column, increment);
    }

    function getCellContent(model, xc) {
        return model.getters.getCell(...toCartesian(xc)).content;
    }

    const LAST_YEAR_FILTER = {
        filter: {
            id: "42",
            type: "date",
            label: "Last Year",
            defaultValue: { year: "last_year" },
            fields: { 1: { field: "date", type: "date" } },
        }
    };

    const THIS_YEAR_FILTER = {
        filter: {
            type: "date",
            label: "This Year",
            defaultValue: { year: "this_year" },
            fields: { 1: { field: "date", type: "date" } },
        }
    };

    QUnit.module(
        "Spreadsheet",
        {
            beforeEach: function () {
                this.data = {
                    "documents.document": {
                        fields: {
                            name: { string: "Name", type: "char" },
                            raw: { string: "Data", type: "text" },
                            thumbnail: { string: "Thumbnail", type: "text" },
                            favorited_ids: { string: "Name", type: "many2many" },
                            is_favorited: { string: "Name", type: "boolean" },
                        },
                        records: [
                            { id: 1, name: "My spreadsheet", raw: "{}", is_favorited: false },
                            { id: 2, name: "", raw: "{}", is_favorited: true },
                        ],
                    },
                    "ir.model": {
                        fields: {
                            name: { string: "Model Name", type: "char" },
                            model: { string: "Model", type: "char" },
                        },
                        records: [
                            {
                                id: 37,
                                name: "Product",
                                model: "product",
                            },
                        ],
                    },
                    partner: {
                        fields: {
                            foo: {
                                string: "Foo",
                                type: "integer",
                                searchable: true,
                                group_operator: "sum",
                            },
                            bar: { string: "bar", type: "boolean", store: true, sortable: true },
                            name: { string: "name", type: "char", store: true, sortable: true },
                            date: { string: "Date", type: "date", store: true, sortable: true },
                            product_id: {
                                string: "Product",
                                type: "many2one",
                                relation: "product",
                                store: true,
                            },
                            probability: {
                                string: "Probability",
                                type: "integer",
                                searchable: true,
                                group_operator: "avg",
                            },
                        },
                        records: [
                            {
                                id: 1,
                                foo: 12,
                                bar: true,
                                date: "2016-04-14",
                                product_id: 37,
                                probability: 10,
                            },
                            {
                                id: 2,
                                foo: 1,
                                bar: true,
                                date: "2016-10-26",
                                product_id: 41,
                                probability: 11,
                            },
                            {
                                id: 3,
                                foo: 17,
                                bar: true,
                                date: "2016-12-15",
                                product_id: 41,
                                probability: 95,
                            },
                            {
                                id: 4,
                                foo: 2,
                                bar: false,
                                date: "2016-12-11",
                                product_id: 41,
                                probability: 15,
                            },
                        ],
                    },
                    product: {
                        fields: {
                            name: { string: "Product Name", type: "char" },
                        },
                        records: [
                            {
                                id: 37,
                                display_name: "xphone",
                            },
                            {
                                id: 41,
                                display_name: "xpad",
                            },
                        ],
                    },
                };
            },
        },
        function () {
            QUnit.module("Spreadsheet export");

            QUnit.test("simple pivot export", async function (assert) {
                assert.expect(8);

                const pivot = await createView({
                    View: PivotView,
                    model: "partner",
                    data: this.data,
                    arch: `
                    <pivot string="Partners">
                        <field name="foo" type="measure"/>
                    </pivot>`,
                    mockRPC: mockRPCFn,
                });
                const data = await pivot._getSpreadsheetData();
                const spreadsheetData = JSON.parse(data);
                const cells = spreadsheetData.sheets[0].cells;
                assert.strictEqual(Object.keys(cells).length, 5);
                assert.strictEqual(cells.A1.content, "");
                assert.strictEqual(cells.A3.content, '=PIVOT.HEADER("1")');
                assert.strictEqual(cells.B1.content, '=PIVOT.HEADER("1")');
                assert.strictEqual(cells.B2.content, '=PIVOT.HEADER("1","measure","foo")');
                assert.strictEqual(cells.B3.content, '=PIVOT("1","foo")');
                assert.strictEqual(cells.B3.format, "#,##0.00");
                assert.strictEqual(spreadsheetData.sheets[0].merges[0], "A1:A2");
                pivot.destroy();
            });

            QUnit.test("groupby week is sorted", async function (assert) {
                assert.expect(3);

                const pivot = await createView({
                    View: PivotView,
                    model: "partner",
                    data: this.data,
                    arch: `
                    <pivot string="Partners">
                        <field name="foo" type="col"/>
                        <field name="date" interval="week" type="row"/>
                        <field name="probability" type="measure"/>
                    </pivot>`,
                    mockRPC: mockRPCFn,
                });
                const model = await pivot._getSpreadsheetModel();
                const cells = model.getters.getSheets()[0].cells
                assert.strictEqual(cells["A3"].content, `=PIVOT.HEADER("1","date:week","16/2016")`);
                assert.strictEqual(cells["A4"].content, `=PIVOT.HEADER("1","date:week","44/2016")`);
                assert.strictEqual(cells["A5"].content, `=PIVOT.HEADER("1","date:week","51/2016")`);
                pivot.destroy();
            });

            QUnit.test("simple pivot export with two measures", async function (assert) {
                assert.expect(12);

                const pivot = await createView({
                    View: PivotView,
                    model: "partner",
                    data: this.data,
                    arch: `
                    <pivot string="Partners">
                        <field name="foo" type="measure"/>
                        <field name="probability" type="measure"/>
                    </pivot>`,
                    mockRPC: mockRPCFn,
                });
                const data = await pivot._getSpreadsheetData();
                const spreadsheetData = JSON.parse(data);
                const cells = spreadsheetData.sheets[0].cells;
                assert.strictEqual(Object.keys(cells).length, 8);
                assert.strictEqual(cells.B1.content, '=PIVOT.HEADER("1")');
                assert.strictEqual(cells.B2.content, '=PIVOT.HEADER("1","measure","foo")');
                assert.strictEqual(
                    spreadsheetData.styles[cells.B2.style].bold,
                    undefined
                );
                assert.strictEqual(
                    cells.C2.content,
                    '=PIVOT.HEADER("1","measure","probability")'
                );
                assert.strictEqual(cells.B3.content, '=PIVOT("1","foo")');
                assert.strictEqual(cells.B3.format, "#,##0.00");
                assert.strictEqual(cells.C3.content, '=PIVOT("1","probability")');
                assert.strictEqual(cells.C3.format, "#,##0.00");
                const merges = spreadsheetData.sheets[0].merges;
                assert.strictEqual(merges.length, 2);
                assert.strictEqual(merges[0], "A1:A2");
                assert.strictEqual(merges[1], "B1:C1");
                pivot.destroy();
            });

            QUnit.test("pivot with two measures: total cells above measures totals are merged in one", async function (assert) {
                assert.expect(2);

                const pivot = await createView({
                    View: PivotView,
                    model: "partner",
                    data: this.data,
                    arch: `
                    <pivot string="Partners">
                        <field name="foo" type="col"/>
                        <field name="date" interval="week" type="row"/>
                        <field name="foo" type="measure"/>
                        <field name="probability" type="measure"/>
                    </pivot>`,
                    mockRPC: mockRPCFn,
                });
                const data = await pivot._getSpreadsheetData();
                const spreadsheetData = JSON.parse(data);
                const merges = spreadsheetData.sheets[0].merges;
                assert.strictEqual(merges.length, 6);
                assert.strictEqual(merges[5], "J1:K1");
                pivot.destroy();
            });

            QUnit.test("pivot with one level of group bys", async function (assert) {
                assert.expect(9);

                const pivot = await createView({
                    View: PivotView,
                    model: "partner",
                    data: this.data,
                    arch: `
                    <pivot string="Partners">
                        <field name="foo" type="col"/>
                        <field name="bar" type="row"/>
                        <field name="probability" type="measure"/>
                    </pivot>`,
                    mockRPC: mockRPCFn,
                });
                const data = await pivot._getSpreadsheetData();
                const spreadsheetData = JSON.parse(data);
                const cells = spreadsheetData.sheets[0].cells;
                assert.strictEqual(Object.keys(cells).length, 29);
                assert.strictEqual(cells.A3.content, '=PIVOT.HEADER("1","bar","false")');
                assert.strictEqual(cells.A4.content, '=PIVOT.HEADER("1","bar","true")');
                assert.strictEqual(cells.A5.content, '=PIVOT.HEADER("1")');
                assert.strictEqual(
                    cells.B2.content,
                    '=PIVOT.HEADER("1","foo","1","measure","probability")'
                );
                assert.strictEqual(
                    cells.C3.content,
                    '=PIVOT("1","probability","bar","false","foo","2")'
                );
                assert.strictEqual(cells.F5.content, '=PIVOT("1","probability")');
                const merges = spreadsheetData.sheets[0].merges;
                assert.strictEqual(merges.length, 1);
                assert.strictEqual(merges[0], "A1:A2");
                pivot.destroy();
            });

            QUnit.test("pivot with two levels of group bys in rows", async function (assert) {
                assert.expect(10);

                const pivot = await createView({
                    View: PivotView,
                    model: "partner",
                    data: this.data,
                    arch: `
                    <pivot string="Partners">
                        <field name="bar" type="row"/>
                        <field name="probability" type="measure"/>
                    </pivot>`,
                    mockRPC: mockRPCFn,
                });
                await testUtils.dom.click(pivot.$("tbody .o_pivot_header_cell_closed:first"));
                await testUtils.dom.click(
                    pivot.$('.o_pivot_field_menu .dropdown-item[data-field="product_id"]:first')
                );
                const data = await pivot._getSpreadsheetData();
                const spreadsheetData = JSON.parse(data);
                const cells = spreadsheetData["sheets"][0]["cells"];
                assert.strictEqual(Object.keys(cells).length, 17);
                assert.strictEqual(cells.A3.content, '=PIVOT.HEADER("1","bar","false")');
                assert.strictEqual(cells.A3.style, 3);
                assert.strictEqual(
                    cells["A4"].content,
                    '=PIVOT.HEADER("1","bar","false","product_id","37")'
                );
                assert.strictEqual(cells.A4.style, 2);
                assert.strictEqual(
                    cells["A5"].content,
                    '=PIVOT.HEADER("1","bar","false","product_id","41")'
                );
                assert.strictEqual(cells["A6"].content, '=PIVOT.HEADER("1","bar","true")');
                assert.strictEqual(
                    cells["A7"].content,
                    '=PIVOT.HEADER("1","bar","true","product_id","37")'
                );
                assert.strictEqual(
                    cells["A8"].content,
                    '=PIVOT.HEADER("1","bar","true","product_id","41")'
                );
                assert.strictEqual(cells["A9"].content, '=PIVOT.HEADER("1")');
                pivot.destroy();
            });

            QUnit.test("verify that there is a record for an undefined header", async function (assert) {
                assert.expect(1);
                this.data.partner.records = [{
                    id: 1,
                    foo: 12,
                    bar: true,
                    date: "2016-04-14",
                    product_id: false,
                    probability: 10,
                }];
                const pivot = await createView({
                    View: PivotView,
                    model: "partner",
                    data: this.data,
                    arch: `
                    <pivot string="Partners">
                        <field name="product_id" type="row"/>
                        <field name="probability" type="measure"/>
                    </pivot>`,
                    mockRPC: mockRPCFn,
                });
                const data = await pivot._getSpreadsheetData();
                const spreadsheetData = JSON.parse(data);
                const cells = spreadsheetData["sheets"][0]["cells"];
                assert.strictEqual(cells["A3"].content, '=PIVOT.HEADER("1","product_id","false")');
                pivot.destroy();
            });

            QUnit.test("undefined date is inserted in pivot", async function (assert) {
                assert.expect(1);
                this.data.partner.records = [{
                    id: 1,
                    foo: 12,
                    bar: true,
                    date: false,
                    product_id: 37,
                    probability: 10,
                }];
                const pivot = await createView({
                    View: PivotView,
                    model: "partner",
                    data: this.data,
                    arch: `
                    <pivot string="Partners">
                        <field name="date" interval="day" type="row"/>
                        <field name="probability" type="measure"/>
                    </pivot>`,
                    mockRPC: mockRPCFn,
                });
                const data = await pivot._getSpreadsheetData();
                const spreadsheetData = JSON.parse(data);
                const cells = spreadsheetData["sheets"][0]["cells"];
                assert.strictEqual(cells["A3"].content, '=PIVOT.HEADER("1","date:day","false")');
                pivot.destroy();
            });

            QUnit.test("pivot with two levels of group bys in cols", async function (assert) {
                assert.expect(14);

                const pivot = await createView({
                    View: PivotView,
                    model: "partner",
                    data: this.data,
                    arch: `
                    <pivot string="Partners">
                        <field name="bar" type="col"/>
                        <field name="probability" type="measure"/>
                    </pivot>`,
                    mockRPC: mockRPCFn,
                });
                await testUtils.dom.click(pivot.$("thead .o_pivot_header_cell_closed:first"));
                await testUtils.dom.click(
                    pivot.$('.o_pivot_field_menu .dropdown-item[data-field="product_id"]:first')
                );
                const data = await pivot._getSpreadsheetData();
                const spreadsheetData = JSON.parse(data);
                const cells = spreadsheetData["sheets"][0]["cells"];

                assert.strictEqual(Object.keys(cells).length, 23);
                assert.strictEqual(cells["A1"].content, '');
                assert.strictEqual(cells["A4"].style, 3);
                assert.strictEqual(
                    cells["B1"].content,
                    '=PIVOT.HEADER("1","bar","false")',
                );
                assert.strictEqual(
                    cells["B2"].content,
                    '=PIVOT.HEADER("1","bar","false","product_id","37")',
                );
                assert.strictEqual(
                    cells["B3"].content,
                    '=PIVOT.HEADER("1","bar","false","product_id","37","measure","probability")',
                );
                assert.strictEqual(cells["C2"].style, 3);
                assert.strictEqual(
                    cells["C2"].content,
                    '=PIVOT.HEADER("1","bar","false","product_id","41")',
                );
                assert.strictEqual(
                    cells["C3"].content,
                    '=PIVOT.HEADER("1","bar","false","product_id","41","measure","probability")',
                );
                assert.strictEqual(
                    cells["D1"].content,
                    '=PIVOT.HEADER("1","bar","true")',
                );
                assert.strictEqual(
                    cells["D2"].content,
                    '=PIVOT.HEADER("1","bar","true","product_id","37")',
                );
                assert.strictEqual(
                    cells["D3"].content,
                    '=PIVOT.HEADER("1","bar","true","product_id","37","measure","probability")',
                );
                assert.strictEqual(
                    cells["E2"].content,
                    '=PIVOT.HEADER("1","bar","true","product_id","41")'
                );
                assert.strictEqual(
                    cells["E3"].content,
                    '=PIVOT.HEADER("1","bar","true","product_id","41","measure","probability")'
                );
                pivot.destroy();
            });

            QUnit.test("pivot with count as measure", async function (assert) {
                assert.expect(3);

                const pivot = await createView({
                    View: PivotView,
                    model: "partner",
                    data: this.data,
                    arch: `
                    <pivot string="Partners">
                        <field name="probability" type="measure"/>
                    </pivot>`,
                    mockRPC: mockRPCFn,
                });
                await testUtils.nextTick();
                await testUtils.pivot.toggleMeasuresDropdown(pivot);
                await testUtils.pivot.clickMeasure(pivot, "__count");
                const data = await pivot._getSpreadsheetData();
                const spreadsheetData = JSON.parse(data);
                const cells = spreadsheetData.sheets[0].cells;
                assert.strictEqual(Object.keys(cells).length, 8);
                assert.strictEqual(cells.C2.content, '=PIVOT.HEADER("1","measure","__count")');
                assert.strictEqual(cells.C3.content, '=PIVOT("1","__count")');
                pivot.destroy();
            });

            QUnit.test("pivot with two levels of group bys in cols with not enough cols", async function (assert) {
                assert.expect(1);

                // add many values in a subgroup
                for (let i = 0; i < 35; i++) {
                    this.data.product.records.push({
                        id: i + 9999,
                        display_name: i.toString(),
                    })
                    this.data.partner.records.push({
                        id: i + 9999,
                        bar: i % 2 === 0,
                        product_id: i + 9999,
                        probability: i,
                    })
                }
                const pivot = await createView({
                    View: PivotView,
                    model: "partner",
                    data: this.data,
                    arch: `
                    <pivot string="Partners">
                        <field name="bar" type="col"/>
                        <field name="foo" type="row"/>
                        <field name="probability" type="measure"/>
                    </pivot>`,
                    mockRPC: mockRPCFn,
                });
                await testUtils.dom.click(pivot.$("thead .o_pivot_header_cell_closed:first"));
                await testUtils.dom.click(
                    pivot.$('.o_pivot_field_menu .dropdown-item[data-field="product_id"]:first')
                );
                const data = await pivot._getSpreadsheetData();
                const spreadsheetData = JSON.parse(data);
                // 37 products * 2 groups + 1 row header + 1 total col + 1 extra empty col at the end
                assert.equal(spreadsheetData.sheets[0].colNumber, 77);
                pivot.destroy();
            });

            QUnit.test("Can save a pivot in a new spreadsheet", async function (assert) {
                assert.expect(2);

                const pivot = await createView({
                    View: PivotView,
                    model: "partner",
                    data: this.data,
                    arch: `
                    <pivot string="Partners">
                        <field name="probability" type="measure"/>
                    </pivot>`,
                    mockRPC: function (route, args) {
                        if (args.method === "search_read" && args.model === "ir.model") {
                            return Promise.resolve([{ name: "partner" }]);
                        }
                        if (route.includes("get_spreadsheets_to_display")) {
                            return Promise.resolve([{ id: 1, name: "My Spreadsheet" }]);
                        }
                        if (args.method === "create" && args.model === "documents.document") {
                            assert.step("create");
                            return Promise.resolve([1]);
                        }
                        return this._super.apply(this, arguments);
                    },
                    session: { user_has_group: async () => true },
                });
                await testUtils.nextTick();
                await testUtils.dom.click(pivot.$el.find(".o_pivot_add_spreadsheet"));
                await testUtils.nextTick();
                await testUtils.modal.clickButton("Confirm");
                await testUtils.nextTick();
                assert.verifySteps(["create"]);
                pivot.destroy();
            });

            QUnit.test("Can save a pivot in existing spreadsheet", async function (assert) {
                assert.expect(4);

                const pivot = await createView({
                    View: PivotView,
                    model: "partner",
                    data: this.data,
                    arch: `
                    <pivot string="Partners">
                        <field name="probability" type="measure"/>
                    </pivot>`,
                    mockRPC: function (route, args) {
                        if (args.method === "search_read" && args.model === "ir.model") {
                            return Promise.resolve([{ name: "partner" }]);
                        }
                        if (args.method === "search_read" && args.model === "documents.document") {
                            assert.step("search_read");
                            return Promise.resolve([{ raw: "{}" }]);
                        }
                        if (route.includes("get_spreadsheets_to_display")) {
                            return Promise.resolve([{ id: 1, name: "My Spreadsheet" }]);
                        }
                        if (args.method === "write" && args.model === "documents.document") {
                            assert.step("write");
                            assert.ok(args.args[0], 1);
                            return Promise.resolve();
                        }
                        return this._super.apply(this, arguments);
                    },
                    session: { user_has_group: async () => true },
                });
                await testUtils.nextTick();
                await testUtils.dom.click(pivot.$el.find(".o_pivot_add_spreadsheet"));
                await testUtils.dom.click($(document.body.querySelector(".modal-content select")));
                document.body.querySelector(".modal-content option[value='1']").setAttribute("selected", "selected");
                await testUtils.nextTick();
                await testUtils.modal.clickButton("Confirm");
                assert.verifySteps(["search_read", "write"]);
                pivot.destroy();
            });

            QUnit.test("Autofill pivot values", async function (assert) {
                assert.expect(26);

                const pivot = await createView({
                    View: PivotView,
                    model: "partner",
                    data: this.data,
                    arch: `
                    <pivot string="Partners">
                        <field name="foo" type="col"/>
                        <field name="bar" type="row"/>
                        <field name="probability" type="measure"/>
                    </pivot>`,
                    mockRPC: mockRPCFn,
                });
                const model = await pivot._getSpreadsheetModel();
                // From value to value
                assert.strictEqual(
                    getAutofillValue(model, "C3", false, 1),
                    getCellContent(model, "C4")
                );
                assert.strictEqual(
                    getAutofillValue(model, "B4", false, -1),
                    getCellContent(model, "B3")
                );
                assert.strictEqual(
                    getAutofillValue(model, "C3", true, 1),
                    getCellContent(model, "D3")
                );
                assert.strictEqual(
                    getAutofillValue(model, "C3", true, -1),
                    getCellContent(model, "B3")
                );
                assert.strictEqual(
                    getAutofillValue(model, "C3", false, 2),
                    getCellContent(model, "C5")
                );
                assert.strictEqual(getAutofillValue(model, "C3", false, 3), "");
                assert.strictEqual(getAutofillValue(model, "C3", true, 4), "");
                // From value to header
                assert.strictEqual(
                    getAutofillValue(model, "B4", true, -1),
                    getCellContent(model, "A4")
                );
                assert.strictEqual(
                    getAutofillValue(model, "B4", false, -1),
                    getCellContent(model, "B3")
                );
                assert.strictEqual(
                    getAutofillValue(model, "B4", false, -2),
                    getCellContent(model, "B2")
                );
                assert.strictEqual(
                    getAutofillValue(model, "B4", false, -3),
                    getCellContent(model, "B1")
                );
                // From header to header
                assert.strictEqual(
                    getAutofillValue(model, "B3", true, 1),
                    getCellContent(model, "C3")
                );
                assert.strictEqual(
                    getAutofillValue(model, "B3", true, 2),
                    getCellContent(model, "D3")
                );
                assert.strictEqual(
                    getAutofillValue(model, "B3", true, -1),
                    getCellContent(model, "A3")
                );
                assert.strictEqual(
                    getAutofillValue(model, "B1", false, 1),
                    getCellContent(model, "B2")
                );
                assert.strictEqual(
                    getAutofillValue(model, "B3", false, -1),
                    getCellContent(model, "B2")
                );
                assert.strictEqual(
                    getAutofillValue(model, "A4", false, 1),
                    getCellContent(model, "A5")
                );
                assert.strictEqual(
                    getAutofillValue(model, "A4", false, -1),
                    getCellContent(model, "A3")
                );
                assert.strictEqual(getAutofillValue(model, "A4", false, 2), "");
                assert.strictEqual(getAutofillValue(model, "A4", false, -3), "");
                // From header to value
                assert.strictEqual(
                    getAutofillValue(model, "B2", false, 1),
                    getCellContent(model, "B3")
                );
                assert.strictEqual(
                    getAutofillValue(model, "B2", false, 2),
                    getCellContent(model, "B4")
                );
                assert.strictEqual(getAutofillValue(model, "B2", false, 4), "");
                assert.strictEqual(
                    getAutofillValue(model, "A3", true, 1),
                    getCellContent(model, "B3")
                );
                assert.strictEqual(
                    getAutofillValue(model, "A3", true, 5),
                    getCellContent(model, "F3")
                );
                assert.strictEqual(getAutofillValue(model, "A3", true, 6), "");
                pivot.destroy();
            });

            QUnit.test("Autofill pivot values with date in rows", async function (assert) {
                assert.expect(5);

                const pivot = await createView({
                    View: PivotView,
                    model: "partner",
                    data: this.data,
                    arch: `
                    <pivot string="Partners">
                        <field name="foo" type="col"/>
                        <field name="date" interval="month" type="row"/>
                        <field name="probability" type="measure"/>
                    </pivot>`,
                    mockRPC: mockRPCFn,
                });
                const model = await pivot._getSpreadsheetModel();
                assert.strictEqual(
                    getAutofillValue(model, "A3", false, 1),
                    getCellContent(model, "A4").replace("10/2016", "05/2016")
                );
                assert.strictEqual(
                    getAutofillValue(model, "A5", false, 1),
                    '=PIVOT.HEADER("1","date:month","01/2017")'
                );
                assert.strictEqual(
                    getAutofillValue(model, "B3", false, 1),
                    getCellContent(model, "B4").replace("10/2016", "05/2016")
                );
                assert.strictEqual(
                    getAutofillValue(model, "B5", false, 1),
                    getCellContent(model, "B5").replace("12/2016", "01/2017")
                );
                assert.strictEqual(
                    getAutofillValue(model, "B5", false, -1),
                    getCellContent(model, "B4").replace("10/2016", "11/2016")
                );
                pivot.destroy();
            });

            QUnit.test("Autofill pivot values with date in cols", async function (assert) {
                assert.expect(3);

                const pivot = await createView({
                    View: PivotView,
                    model: "partner",
                    data: this.data,
                    arch: `
                    <pivot string="Partners">
                        <field name="foo" type="row"/>
                        <field name="date" interval="day" type="col"/>
                        <field name="probability" type="measure"/>
                    </pivot>`,
                    mockRPC: mockRPCFn,
                });
                const model = await pivot._getSpreadsheetModel();
                assert.strictEqual(
                    getAutofillValue(model, "B1", true, 1),
                    getCellContent(model, "B1").replace("20/01/2016", "21/01/2016")
                );
                assert.strictEqual(
                    getAutofillValue(model, "B2", true, 1),
                    getCellContent(model, "B2").replace("20/01/2016", "21/01/2016")
                );
                assert.strictEqual(
                    getAutofillValue(model, "B3", true, 1),
                    getCellContent(model, "B3").replace("20/01/2016", "21/01/2016")
                );
                pivot.destroy();
            });

            QUnit.test("Autofill pivot values with date (day)", async function (assert) {
                assert.expect(1);

                const pivot = await createView({
                    View: PivotView,
                    model: "partner",
                    data: this.data,
                    arch: `
                    <pivot string="Partners">
                        <field name="foo" type="col"/>
                        <field name="date" interval="day" type="row"/>
                        <field name="probability" type="measure"/>
                    </pivot>`,
                    mockRPC: mockRPCFn,
                });
                const model = await pivot._getSpreadsheetModel();
                assert.strictEqual(
                    getAutofillValue(model, "A3", false, 1),
                    getCellContent(model, "A3").replace("20/01/2016", "21/01/2016")
                );
                pivot.destroy();
            });

            QUnit.test("Autofill pivot values with date (quarter)", async function (assert) {
                assert.expect(1);

                const pivot = await createView({
                    View: PivotView,
                    model: "partner",
                    data: this.data,
                    arch: `
                    <pivot string="Partners">
                        <field name="foo" type="col"/>
                        <field name="date" interval="quarter" type="row"/>
                        <field name="probability" type="measure"/>
                    </pivot>`,
                    mockRPC: mockRPCFn,
                });
                const model = await pivot._getSpreadsheetModel();
                assert.strictEqual(
                    getAutofillValue(model, "A3", false, 1),
                    getCellContent(model, "A3").replace("2/2016", "3/2016")
                );
                pivot.destroy();
            });

            QUnit.test("Autofill pivot values with date (year)", async function (assert) {
                assert.expect(1);

                const pivot = await createView({
                    View: PivotView,
                    model: "partner",
                    data: this.data,
                    arch: `
                    <pivot string="Partners">
                        <field name="foo" type="col"/>
                        <field name="date" interval="year" type="row"/>
                        <field name="probability" type="measure"/>
                    </pivot>`,
                    mockRPC: mockRPCFn,
                });
                const model = await pivot._getSpreadsheetModel();
                assert.strictEqual(
                    getAutofillValue(model, "A3", false, 1),
                    getCellContent(model, "A3").replace("2016", "2017")
                );
                pivot.destroy();
            });

            QUnit.test("pivot ids are correctly assigned", async function (assert) {
                assert.expect(3);

                const pivot = await createView({
                    View: PivotView,
                    model: "partner",
                    data: this.data,
                    arch: `
                    <pivot string="Partners">
                        <field name="foo" type="col"/>
                        <field name="bar" type="row"/>
                        <field name="probability" type="measure"/>
                    </pivot>`,
                    mockRPC: mockRPCFn,
                });
                const model = await pivot._getSpreadsheetModel();
                const [ p1 ] = Object.values(model.getters.getPivots());
                assert.strictEqual(p1.id, 1, "It should have id 1");
                const [ p2, p3 ] = [ Object.assign({}, p1), Object.assign({}, p1) ];
                model.dispatch("ADD_PIVOT", {
                    anchor: [12, 0],
                    pivot: p2,
                });
                assert.deepEqual(
                    Object.values(model.getters.getPivots()).map((p) => p.id), [1, 2],
                    "Last pivot should have id 2",
                );
                model.dispatch("ADD_PIVOT", {
                    anchor: [12, 0],
                    pivot: p3,
                });
                assert.deepEqual(
                    Object.values(model.getters.getPivots()).map((p) => p.id), [1, 2, 3],
                    "Last pivot should have id 3",
                );
                pivot.destroy();
            });

            QUnit.test("pivot with a domain", async function (assert) {
                assert.expect(3);

                const pivot = await createView({
                    View: PivotView,
                    model: "partner",
                    data: this.data,
                    domain: [["bar", "=", true]],
                    arch: `
                    <pivot string="Partners">
                        <field name="foo" type="col"/>
                        <field name="bar" type="row"/>
                        <field name="probability" type="measure"/>
                    </pivot>`,
                    mockRPC: mockRPCFn,
                });
                const model = await pivot._getSpreadsheetModel();
                const [p1] = Object.values(model.getters.getPivots());
                assert.deepEqual(
                    p1.domain,
                    [["bar", "=", true]],
                    "It should have the correct domain"
                );
                assert.equal(
                    model.getters.getCell(0, 2).content,
                    `=PIVOT.HEADER("1","bar","true")`
                );
                assert.equal(model.getters.getCell(0, 3).content, `=PIVOT.HEADER("1")`);
                pivot.destroy();
            });

            QUnit.test("Insert in spreadsheet is disabled when no measure is specified", async function (assert) {
                assert.expect(1);
                const pivot = await createView({
                    View: PivotView,
                    model: "partner",
                    data: this.data,
                    arch: `
                    <pivot string="Partners">
                        <field name="foo" type="measure"/>
                    </pivot>`,
                    mockRPC: mockRPCFn,
                    session: { user_has_group: async () => true },
                });
                await testUtils.pivot.toggleMeasuresDropdown(pivot);
                await testUtils.pivot.clickMeasure(pivot, 'foo');
                assert.ok(document.body.querySelector("button.o_pivot_add_spreadsheet").disabled);
                pivot.destroy();
            });

            QUnit.test("Insert in spreadsheet is disabled when data is empty", async function (assert) {
                assert.expect(1);
                const data = Object.assign({}, this.data);
                data.partner.records = [];
                data.product.records = [];
                const pivot = await createView({
                    View: PivotView,
                    model: "partner",
                    data: data,
                    arch: `
                    <pivot string="Partners">
                        <field name="foo" type="measure"/>
                    </pivot>`,
                    mockRPC: mockRPCFn,
                    session: { user_has_group: async () => true },
                });
                assert.ok(document.body.querySelector("button.o_pivot_add_spreadsheet").disabled);
                pivot.destroy();
            });

            QUnit.test("Can add a global filter", async function (assert) {
                assert.expect(4);
                const pivotCtrl = await createView({
                    View: PivotView,
                    model: "partner",
                    data: this.data,
                    arch: `
                    <pivot string="Partners">
                        <field name="foo" type="col"/>
                        <field name="bar" type="row"/>
                        <field name="probability" type="measure"/>
                    </pivot>`,
                    mockRPC: mockRPCFn,
                });
                const model = await pivotCtrl._getSpreadsheetModel();
                assert.equal(model.getters.getGlobalFilters().length, 0);
                const [ pivot ] = model.getters.getPivots();
                model.dispatch("ADD_PIVOT_FILTER", LAST_YEAR_FILTER);
                assert.equal(model.getters.getGlobalFilters().length, 1);
                assert.equal(pivot.computedDomain.length, 3);
                assert.equal(pivot.computedDomain[0], "&");
                pivotCtrl.destroy();
            });

            QUnit.test("Can delete a global filter", async function (assert) {
                assert.expect(4);
                const pivotCtrl = await createView({
                    View: PivotView,
                    model: "partner",
                    data: this.data,
                    arch: `
                    <pivot string="Partners">
                        <field name="foo" type="col"/>
                        <field name="bar" type="row"/>
                        <field name="probability" type="measure"/>
                    </pivot>`,
                    mockRPC: mockRPCFn,
                });
                const model = await pivotCtrl._getSpreadsheetModel();
                assert.deepEqual(model.dispatch("REMOVE_PIVOT_FILTER", { id: 1 }), { status: "CANCELLED", reason: CancelledReason.FilterNotFound });
                model.dispatch("ADD_PIVOT_FILTER", LAST_YEAR_FILTER);
                const gf = model.getters.getGlobalFilters()[0];
                assert.deepEqual(model.dispatch("REMOVE_PIVOT_FILTER", { id: gf.id }), { status: "SUCCESS" });
                assert.equal(model.getters.getGlobalFilters().length, 0);
                const [ pivot ] = model.getters.getPivots();
                assert.equal(pivot.computedDomain.length, 0);
                pivotCtrl.destroy();
            });

            QUnit.test("Can edit a global filter", async function (assert) {
                assert.expect(4);
                const pivotCtrl = await createView({
                    View: PivotView,
                    model: "partner",
                    data: this.data,
                    arch: `
                    <pivot string="Partners">
                        <field name="foo" type="col"/>
                        <field name="bar" type="row"/>
                        <field name="probability" type="measure"/>
                    </pivot>`,
                    mockRPC: mockRPCFn,
                });
                const model = await pivotCtrl._getSpreadsheetModel();
                const gfDef = Object.assign({}, THIS_YEAR_FILTER, { id: 1 });
                assert.deepEqual(model.dispatch("EDIT_PIVOT_FILTER", gfDef), { status: "CANCELLED", reason: CancelledReason.FilterNotFound });
                model.dispatch("ADD_PIVOT_FILTER", LAST_YEAR_FILTER);
                const gf = model.getters.getGlobalFilters()[0];
                gfDef.id = gf.id;
                assert.deepEqual(model.dispatch("EDIT_PIVOT_FILTER", gfDef), { status: "SUCCESS" });
                assert.equal(model.getters.getGlobalFilters().length, 1);
                assert.deepEqual(model.getters.getGlobalFilters()[0].defaultValue.year, "this_year");
                pivotCtrl.destroy();
            });

            QUnit.test("Cannot have duplicated names", async function (assert) {
                assert.expect(6);
                const pivotCtrl = await createView({
                    View: PivotView,
                    model: "partner",
                    data: this.data,
                    arch: `
                    <pivot string="Partners">
                        <field name="foo" type="col"/>
                        <field name="bar" type="row"/>
                        <field name="probability" type="measure"/>
                    </pivot>`,
                    mockRPC: mockRPCFn,
                });
                const model = await pivotCtrl._getSpreadsheetModel();
                const filter = Object.assign({}, THIS_YEAR_FILTER.filter, { label: "Hello" });
                model.dispatch("ADD_PIVOT_FILTER", { filter });
                assert.equal(model.getters.getGlobalFilters().length, 1);

                // Add filter with same name
                let result = model.dispatch("ADD_PIVOT_FILTER", Object.assign({ id: "456" }, { filter }));
                assert.deepEqual(result, { status: "CANCELLED", reason: CancelledReason.DuplicatedFilterLabel });
                assert.equal(model.getters.getGlobalFilters().length, 1);

                // Edit to set same name as other filter
                model.dispatch("ADD_PIVOT_FILTER", { filter: Object.assign({ id: "789" }, filter, { label: "Other name" }) });
                assert.equal(model.getters.getGlobalFilters().length, 2);
                result = model.dispatch("EDIT_PIVOT_FILTER", {id: "789", filter: Object.assign({}, filter, { label: "Hello" }) });
                assert.deepEqual(result, { status: "CANCELLED", reason: CancelledReason.DuplicatedFilterLabel });

                // Edit to set same name
                result = model.dispatch("EDIT_PIVOT_FILTER", {id: "789", filter: Object.assign({}, filter, { label: "Other name" }) });
                assert.deepEqual(result, { status: "SUCCESS" });

                pivotCtrl.destroy();
            });

            QUnit.test("Can save a value to an existing global filter", async function (assert) {
                assert.expect(7);
                const pivotCtrl = await createView({
                    View: PivotView,
                    model: "partner",
                    data: this.data,
                    arch: `
                    <pivot string="Partners">
                        <field name="foo" type="col"/>
                        <field name="bar" type="row"/>
                        <field name="probability" type="measure"/>
                    </pivot>`,
                    mockRPC: mockRPCFn,
                });
                const model = await pivotCtrl._getSpreadsheetModel();
                model.dispatch("ADD_PIVOT_FILTER", LAST_YEAR_FILTER);
                const gf = model.getters.getGlobalFilters()[0];
                assert.deepEqual(model.dispatch("SET_PIVOT_FILTER_VALUE", { id: gf.id, value: { period: "last_month" } }), { status: "SUCCESS" });
                assert.equal(model.getters.getGlobalFilters().length, 1);
                assert.deepEqual(model.getters.getGlobalFilters()[0].defaultValue.year, "last_year");
                assert.deepEqual(model.getters.getGlobalFilters()[0].value.period, "last_month");
                assert.deepEqual(model.dispatch("SET_PIVOT_FILTER_VALUE", { id: gf.id, value: { period: "this_month" } }), { status: "SUCCESS" });
                assert.deepEqual(model.getters.getGlobalFilters()[0].value.period, "this_month");
                const [ pivot ] = model.getters.getPivots();
                assert.equal(pivot.computedDomain.length, 3);
                pivotCtrl.destroy();
            });

            QUnit.test("Can export/import filters", async function (assert) {
                assert.expect(4);
                const pivotCtrl = await createView({
                    View: PivotView,
                    model: "partner",
                    data: this.data,
                    arch: `
                    <pivot string="Partners">
                        <field name="foo" type="col"/>
                        <field name="bar" type="row"/>
                        <field name="probability" type="measure"/>
                    </pivot>`,
                    mockRPC: mockRPCFn,
                });
                const model = await pivotCtrl._getSpreadsheetModel();
                model.dispatch("ADD_PIVOT_FILTER", LAST_YEAR_FILTER);
                const newModel = new Model(model.exportData(), {
                    evalContext: {
                        env: {
                            services: {
                                rpc: () => [],
                            },
                        },
                    },
                });
                assert.equal(newModel.getters.getGlobalFilters().length, 1);
                const [filter] = newModel.getters.getGlobalFilters();
                assert.deepEqual(filter.defaultValue.year, "last_year");
                assert.deepEqual(filter.value.year, "last_year", "it should have applied the default value");

                const [ pivot ] = newModel.getters.getPivots();
                assert.equal(pivot.computedDomain.length, 3, "it should have updated the pivot domain");
                pivotCtrl.destroy();
            });

            QUnit.skip("It only loads pivot cache once", async function (assert) {
                assert.expect(7);
                const pivotCtrl = await createView({
                    View: PivotView,
                    model: "partner",
                    data: this.data,
                    arch: `
                    <pivot string="Partners">
                        <field name="foo" type="col"/>
                        <field name="bar" type="row"/>
                        <field name="probability" type="measure"/>
                    </pivot>`,
                    mockRPC: mockRPCFn,
                });
                const model = await pivotCtrl._getSpreadsheetModel();
                model.dispatch("ADD_PIVOT_FILTER", LAST_YEAR_FILTER);
                const newModel = new Model(model.exportData(), {
                    evalContext: {
                        env: {
                            services: {
                                rpc: (params) => {
                                    if (params.method === "read_group") {
                                        assert.step("load_cache")
                                        assert.equal(params.domain.length, 3, "it should have the filter domain")
                                    }
                                    return []
                                },
                            },
                        },
                    },
                });
                assert.equal(newModel.getters.getGlobalFilters().length, 1);
                const [ pivot ] = newModel.getters.getPivots();
                assert.equal(pivot.computedDomain.length, 3, "it should have updated the pivot domain");
                assert.verifySteps(["load_cache"])
                pivotCtrl.destroy();
            });

            QUnit.test("Relational filter with undefined value", async function (assert) {
                assert.expect(1);
                const pivotCtrl = await createView({
                    View: PivotView,
                    model: "partner",
                    data: this.data,
                    arch: `
                    <pivot string="Partners">
                        <field name="foo" type="col"/>
                        <field name="bar" type="row"/>
                        <field name="probability" type="measure"/>
                    </pivot>`,
                    mockRPC: mockRPCFn,
                });
                const model = await pivotCtrl._getSpreadsheetModel();
                model.dispatch("ADD_PIVOT_FILTER", {
                    filter: {
                        id: "42",
                        type: "relation",
                        label: "Relation Filter",
                        fields: {
                            1: {
                                field: "foo",
                                type: "char",
                            },
                        },
                    },
                });
                const [filter] = model.getters.getGlobalFilters();
                model.dispatch("SET_PIVOT_FILTER_VALUE", {
                    id: filter.id,
                    value: undefined,
                });
                const [ pivot ] = model.getters.getPivots();
                assert.equal(pivot.computedDomain.length, 0, "it should not have updated the pivot domain");
                pivotCtrl.destroy();
            });

            QUnit.test("Get active filters with multiple filters", async function (assert) {
                assert.expect(2);
                const model = new Model();
                model.dispatch("ADD_PIVOT_FILTER", {
                    filter: {
                        id: "42",
                        type: "text",
                        label: "Text Filter",
                    },
                });
                model.dispatch("ADD_PIVOT_FILTER", {
                    filter: {
                        id: "43",
                        type: "date",
                        label: "Date Filter",
                        rangeType: "quarter",
                    },
                });
                model.dispatch("ADD_PIVOT_FILTER", {
                    filter: {
                        id: "44",
                        type: "relation",
                        label: "Relation Filter",
                    },
                });
                const [text, date, relation] = model.getters.getGlobalFilters();
                assert.equal(model.getters.getActiveFilterCount(), false);
                model.dispatch("SET_PIVOT_FILTER_VALUE", {
                    id: text.id,
                    value: "Hello",
                });
                assert.equal(model.getters.getActiveFilterCount(), true);
            });

            QUnit.test("Get active filters with text filter enabled", async function (assert) {
                assert.expect(2);
                const model = new Model();
                model.dispatch("ADD_PIVOT_FILTER", {
                    filter: {
                        id: "42",
                        type: "text",
                        label: "Text Filter",
                    },
                });
                const [filter] = model.getters.getGlobalFilters();
                assert.equal(model.getters.getActiveFilterCount(), false);
                model.dispatch("SET_PIVOT_FILTER_VALUE", {
                    id: filter.id,
                    value: "Hello",
                });
                assert.equal(model.getters.getActiveFilterCount(), true);
            });

            QUnit.test("Get active filters with relation filter enabled", async function (assert) {
                assert.expect(2);
                const model = new Model();
                model.dispatch("ADD_PIVOT_FILTER", {
                    filter: {
                        id: "42",
                        type: "relation",
                        label: "Relation Filter",
                    },
                });
                const [filter] = model.getters.getGlobalFilters();
                assert.equal(model.getters.getActiveFilterCount(), false);
                model.dispatch("SET_PIVOT_FILTER_VALUE", {
                    id: filter.id,
                    value: [1],
                });
                assert.equal(model.getters.getActiveFilterCount(), true);
            });

            QUnit.test("Get active filters with date filter enabled", async function (assert) {
                assert.expect(4);
                const model = new Model();
                model.dispatch("ADD_PIVOT_FILTER", {
                    filter: {
                        id: "42",
                        type: "date",
                        label: "Date Filter",
                        rangeType: "quarter",
                    },
                });
                const [filter] = model.getters.getGlobalFilters();
                assert.equal(model.getters.getActiveFilterCount(), false);
                model.dispatch("SET_PIVOT_FILTER_VALUE", {
                    id: filter.id,
                    value: {
                        year: "this_year",
                        period: undefined,
                    },
                });
                assert.equal(model.getters.getActiveFilterCount(), true);
                model.dispatch("SET_PIVOT_FILTER_VALUE", {
                    id: filter.id,
                    value: {
                        year: undefined,
                        period: "first_quarter",
                    },
                });
                assert.equal(model.getters.getActiveFilterCount(), true);
                model.dispatch("SET_PIVOT_FILTER_VALUE", {
                    id: filter.id,
                    value: {
                        year: "this_year",
                        period: "first_quarter",
                    },
                });
                assert.equal(model.getters.getActiveFilterCount(), true);
            });

            QUnit.test("FILTER.VALUE text filter", async function (assert) {
                assert.expect(3);
                const model = new Model();
                model.dispatch("SET_VALUE", { xc: "A10", text: `=FILTER.VALUE("Text Filter")` });
                await testUtils.nextTick();
                assert.equal(model.getters.getCell(0, 9).value, "#ERROR");
                model.dispatch("ADD_PIVOT_FILTER", {
                    filter: {
                        id: "42",
                        type: "text",
                        label: "Text Filter",
                        fields: {
                            1: {
                                field: "name",
                                type: "char",
                            },
                        },
                    },
                });
                await testUtils.nextTick();
                assert.equal(model.getters.getCell(0, 9).value, "");
                const [filter] = model.getters.getGlobalFilters();
                model.dispatch("SET_PIVOT_FILTER_VALUE", {
                    id: filter.id,
                    value: "Hello",
                });
                await testUtils.nextTick();
                assert.equal(model.getters.getCell(0, 9).value, "Hello");
            });

            QUnit.test("FILTER.VALUE date filter", async function (assert) {
                assert.expect(2);
                const model = new Model();
                model.dispatch("SET_VALUE", { xc: "A10", text: `=FILTER.VALUE("Date Filter")` });
                await testUtils.nextTick();
                model.dispatch("ADD_PIVOT_FILTER", {
                    filter: {
                        id: "42",
                        type: "date",
                        label: "Date Filter",
                        fields: {
                            1: {
                                field: "name",
                                type: "char",
                            },
                        },
                    },
                });
                await testUtils.nextTick();
                const [filter] = model.getters.getGlobalFilters();
                model.dispatch("SET_PIVOT_FILTER_VALUE", {
                    id: filter.id,
                    rangeType: "quarter",
                    value: {
                        year: "this_year",
                        period: "first_quarter",
                    },
                });
                await testUtils.nextTick();
                assert.equal(model.getters.getCell(0, 9).value, `Q1 ${moment().year()}`);
                model.dispatch("SET_PIVOT_FILTER_VALUE", {
                    id: filter.id,
                    rangeType: "year",
                    value: {
                        year: "this_year",
                    },
                });
                await testUtils.nextTick();
                assert.equal(model.getters.getCell(0, 9).value, `${moment().year()}`);
            });

            QUnit.test("FILTER.VALUE relation filter", async function (assert) {
                assert.expect(6);
                const model = new Model(
                    {},
                    {
                        evalContext: {
                            env: {
                                services: {
                                    rpc: async (params) => {
                                        const resId = params.args[0][0]
                                        assert.step(`name_get_${resId}`)
                                        return resId === 1
                                            ? [[1, "Jean-Jacques"]]
                                            : [[2, "Raoul Grosbedon"]]
                                    }
                                },
                            },
                        },
                    }
                );
                model.dispatch("SET_VALUE", {
                    xc: "A10",
                    text: `=FILTER.VALUE("Relation Filter")`,
                });
                await testUtils.nextTick();
                model.dispatch("ADD_PIVOT_FILTER", {
                    filter: {
                        id: "42",
                        type: "relation",
                        label: "Relation Filter",
                        modelName: "partner",
                    },
                });
                await testUtils.nextTick();
                const [filter] = model.getters.getGlobalFilters();

                // One record; displayNames not defined => rpc
                model.dispatch("SET_PIVOT_FILTER_VALUE", {
                    id: filter.id,
                    value: [1],
                });
                await testUtils.nextTick();
                assert.equal(model.getters.getCell(0, 9).value, "Jean-Jacques");

                // Two records; displayNames defined => no rpc
                model.dispatch("SET_PIVOT_FILTER_VALUE", {
                    id: filter.id,
                    value: [1, 2],
                    displayNames: ["Jean-Jacques", "Raoul Grosbedon"],
                });
                await testUtils.nextTick();
                assert.equal(model.getters.getCell(0, 9).value, "Jean-Jacques, Raoul Grosbedon");

                // another record; displayNames not defined => rpc
                model.dispatch("SET_PIVOT_FILTER_VALUE", {
                    id: filter.id,
                    value: [2],
                });
                await testUtils.nextTick();
                assert.equal(model.getters.getCell(0, 9).value, "Raoul Grosbedon");
                assert.verifySteps(["name_get_1", "name_get_2"]);
            });

            QUnit.test(
                "FILTER.VALUE formulas are updated when filter label is changed",
                async function (assert) {
                    assert.expect(1);
                    const model = new Model();
                    model.dispatch("ADD_PIVOT_FILTER", {
                        filter: {
                            id: "42",
                            type: "date",
                            label: "Cuillère",
                            fields: {
                                1: {
                                    field: "name",
                                    type: "char",
                                },
                            },
                        },
                    });
                    model.dispatch("SET_VALUE", {
                        xc: "A10",
                        text: `=FILTER.VALUE("Cuillère") & FILTER.VALUE( "Cuillère" )`,
                    });
                    const [filter] = model.getters.getGlobalFilters();
                    const newFilter = {
                        type: "date",
                        label: "Interprete",
                        fields: {
                            1: {
                                field: "name",
                                type: "char",
                            },
                        },
                    };
                    model.dispatch("EDIT_PIVOT_FILTER", { id: filter.id, filter: newFilter });
                    assert.equal(
                        model.getters.getCell(0, 9).content,
                        `=FILTER.VALUE("Interprete") & FILTER.VALUE("Interprete")`
                    );
                }
            );

            QUnit.test("Exporting data does not remove value from model",
                async function (assert) {
                    assert.expect(2);
                    const model = new Model();
                    model.dispatch("ADD_PIVOT_FILTER", {
                        filter: {
                            id: "42",
                            type: "text",
                            label: "Cuillère",
                            fields: {
                                1: {
                                    field: "name",
                                    type: "char",
                                },
                            },
                        },
                    });
                    model.dispatch("SET_PIVOT_FILTER_VALUE", {
                        id: "42",
                        value: "Hello export bug",
                    });
                    const [filter] = model.getters.getGlobalFilters();
                    assert.equal(filter.value, "Hello export bug");
                    model.exportData();
                    assert.equal(filter.value, "Hello export bug");
                }
            );

            QUnit.test("Tooltip of pivot formulas", async function (assert) {
                assert.expect(6);

                const [actionManager, model, env] = await createSpreadsheetFromPivot({
                    model: "partner",
                    data: this.data,
                    arch: `
                    <pivot string="Partners">
                        <field name="foo" type="col"/>
                        <field name="date" interval="year" type="row"/>
                        <field name="probability" type="measure"/>
                    </pivot>`,
                    mockRPC: mockRPCFn,
                });
                const spreadsheetAction = actionManager.getCurrentController().widget;
                await Promise.all(
                    Object.values(model.getters.getPivots()).map((pivot) =>
                        pivotUtils.fetchCache(pivot, spreadsheetAction._rpc.bind(spreadsheetAction))
                    )
                );
                assert.deepEqual(model.getters.getTooltipFormula(getCellContent(model, "A3")), [{
                    "title": "Date (Year)",
                    "value": "2016"
                }]);
                assert.deepEqual(model.getters.getTooltipFormula(getCellContent(model, "B3")), [{
                    "title": "Date (Year)",
                    "value": "2016"
                }]);
                assert.deepEqual(model.getters.getTooltipFormula(getCellContent(model, "E3")), [{
                    "title": "Date (Year)",
                    "value": "2016"
                }]);
                assert.deepEqual(model.getters.getTooltipFormula(getCellContent(model, "F3")), [{
                    "title": "Date (Year)",
                    "value": "2016"
                }]);
                assert.deepEqual(model.getters.getTooltipFormula(getCellContent(model, "B1")), [{
                    "title": "Foo",
                    "value": 1
                }]);
                assert.deepEqual(model.getters.getTooltipFormula(getCellContent(model, "B2")), [{
                    "title": "Foo",
                    "value": 1
                }, {
                    "title": "Measure",
                    "value": "Probability"
                }]);
                actionManager.destroy();
            });

            QUnit.test("Tooltip of pivot formulas with 2 measures", async function (assert) {
                assert.expect(3);

                const [actionManager, model, env] = await createSpreadsheetFromPivot({
                    model: "partner",
                    data: this.data,
                    arch: `
                    <pivot string="Partners">
                        <field name="name" type="col"/>
                        <field name="date" interval="year" type="row"/>
                        <field name="probability" type="measure"/>
                        <field name="foo" type="measure"/>
                    </pivot>`,
                    mockRPC: mockRPCFn,
                });
                const spreadsheetAction = actionManager.getCurrentController().widget;
                await Promise.all(
                    Object.values(model.getters.getPivots()).map((pivot) =>
                        pivotUtils.fetchCache(pivot, spreadsheetAction._rpc.bind(spreadsheetAction))
                    )
                );
                assert.deepEqual(model.getters.getTooltipFormula(getCellContent(model, "A3")), [{
                    "title": "Date (Year)",
                    "value": "2016"
                }]);
                assert.deepEqual(model.getters.getTooltipFormula(getCellContent(model, "B3")), [{
                    "title": "Date (Year)",
                    "value": "2016"
                }, {
                    "title": "Measure",
                    "value": "Probability"
                }]);
                assert.deepEqual(model.getters.getTooltipFormula(getCellContent(model, "C3")), [{
                    "title": "Date (Year)",
                    "value": "2016"
                }, {
                    "title": "Measure",
                    "value": "Foo"
                }]);
                actionManager.destroy();
            });

            QUnit.test("Tooltip of empty pivot formula is empty", async function (assert) {
                assert.expect(1);

                const [actionManager, model, env] = await createSpreadsheetFromPivot({
                    model: "partner",
                    data: this.data,
                    arch: `
                    <pivot string="Partners">
                        <field name="name" type="col"/>
                        <field name="date" interval="year" type="row"/>
                        <field name="probability" type="measure"/>
                        <field name="foo" type="measure"/>
                    </pivot>`,
                    mockRPC: mockRPCFn,
                });
                const spreadsheetAction = actionManager.getCurrentController().widget;
                await Promise.all(
                    Object.values(model.getters.getPivots()).map((pivot) =>
                        pivotUtils.fetchCache(pivot, spreadsheetAction._rpc.bind(spreadsheetAction))
                    )
                );
                model.dispatch("SELECT_CELL", { col: 0, row: 2 });
                model.dispatch("AUTOFILL_SELECT", { col: 10, row: 10 });
                assert.equal(model.getters.getAutofillTooltip(), undefined);
                actionManager.destroy();
            });

            QUnit.test("Re-insert a pivot with a global filter should re-insert the full pivot", async function (assert) {
                assert.expect(1);

                const [actionManager, model, env] = await createSpreadsheetFromPivot({
                    model: "partner",
                    data: this.data,
                    arch: `
                    <pivot string="Partners">
                        <field name="product_id" type="col"/>
                        <field name="name" type="row"/>
                        <field name="probability" type="measure"/>
                    </pivot>`,
                    mockRPC: mockRPCFn,
                });
                model.dispatch("ADD_PIVOT_FILTER", {
                    filter: {
                        id: "41",
                        type: "relation",
                        label: "41",
                        defaultValue: [41],
                        fields: { 1: { field: "product_id", type: "many2one" } },
                    }
                });
                model.dispatch("SELECT_CELL", { col: 0, row: 5 });
                const root = cellMenuRegistry.getAll().find((item) => item.id === "reinsert_pivot");
                const reinsertPivot = cellMenuRegistry.getChildren(root, env)[0];
                await reinsertPivot.action(env);
                await testUtils.nextTick();
                assert.equal(getCellContent(model, "B6"), getCellContent(model, "B1"));
                actionManager.destroy();
            });
        }
    );
});
