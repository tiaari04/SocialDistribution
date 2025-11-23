"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getRelease = exports.all = exports.arbitraryAppDB = void 0;
const debug_1 = require("debug");
const lodash_1 = require("lodash");
const pgDebug = (0, debug_1.default)('pg');
async function arbitraryAppDB(heroku, app) {
    // Since Postgres backups are tied to the app and not the add-on, but
    // we require *an* add-on to interact with, make sure that add-on is
    // attached to the right app.
    pgDebug(`fetching arbitrary app db on ${app}`);
    const { body: addons } = await heroku.get(`/apps/${app}/addons`);
    const addon = addons.find(a => { var _a, _b, _c; return ((_a = a === null || a === void 0 ? void 0 : a.app) === null || _a === void 0 ? void 0 : _a.name) === app && ((_c = (_b = a === null || a === void 0 ? void 0 : a.plan) === null || _b === void 0 ? void 0 : _b.name) === null || _c === void 0 ? void 0 : _c.startsWith('heroku-postgresql')); });
    if (!addon)
        throw new Error(`No heroku-postgresql databases on ${app}`);
    return addon;
}
exports.arbitraryAppDB = arbitraryAppDB;
function getAttachmentNamesByAddon(attachments) {
    return attachments.reduce((results, a) => {
        results[a.addon.id] = (results[a.addon.id] || []).concat(a.name);
        return results;
    }, {});
}
async function all(heroku, app_id) {
    pgDebug(`fetching all DBs on ${app_id}`);
    const attachments = await allAttachments(heroku, app_id);
    let addons = attachments.map(a => a.addon);
    // Get the list of attachment names per addon here and add to each addon obj
    const attachmentNamesByAddon = getAttachmentNamesByAddon(attachments);
    addons = (0, lodash_1.uniqBy)(addons, 'id');
    addons.forEach(addon => {
        addon.attachment_names = attachmentNamesByAddon[addon.id];
    });
    return addons;
}
exports.all = all;
async function allAttachments(heroku, app_id) {
    const { body: attachments } = await heroku.get(`/apps/${app_id}/addon-attachments`, {
        headers: { 'Accept-Inclusion': 'addon:plan,config_vars' },
    });
    return attachments.filter((a) => { var _a, _b; return (_b = (_a = a.addon.plan) === null || _a === void 0 ? void 0 : _a.name) === null || _b === void 0 ? void 0 : _b.startsWith('heroku-postgresql'); });
}
async function getRelease(heroku, appName, id) {
    const { body: release } = await heroku.get(`/apps/${appName}/releases/${id}`);
    return release;
}
exports.getRelease = getRelease;
