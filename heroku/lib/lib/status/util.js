"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getMaxUpdateTypeLength = void 0;
function getMaxUpdateTypeLength(updateTypes) {
    let max = 0;
    for (const update of updateTypes) {
        if (!max || update.length > max) {
            max = update.length;
        }
    }
    return max;
}
exports.getMaxUpdateTypeLength = getMaxUpdateTypeLength;
