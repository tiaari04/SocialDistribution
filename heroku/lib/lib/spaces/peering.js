"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.displayPeerings = exports.displayPeeringsAsJSON = exports.displayPeeringInfo = void 0;
const core_1 = require("@oclif/core");
const heroku_cli_util_1 = require("@heroku/heroku-cli-util");
const format_1 = require("./format");
function displayPeeringInfo(space, info) {
    heroku_cli_util_1.hux.styledHeader(`${space} Peering Info`);
    heroku_cli_util_1.hux.styledObject({
        'AWS Account ID': info.aws_account_id,
        'AWS Region': info.aws_region,
        'AWS VPC ID': info.vpc_id,
        'AWS VPC CIDR': info.vpc_cidr,
        'Space CIDRs': (0, format_1.displayCIDR)(info.space_cidr_blocks),
        'Unavailable CIDRs': (0, format_1.displayCIDR)(info.unavailable_cidr_blocks),
    }, ['AWS Account ID', 'AWS Region', 'AWS VPC ID', 'AWS VPC CIDR', 'Space CIDRs', 'Unavailable CIDRs']);
}
exports.displayPeeringInfo = displayPeeringInfo;
function displayPeeringsAsJSON(peerings) {
    core_1.ux.log(JSON.stringify(peerings, null, 2));
}
exports.displayPeeringsAsJSON = displayPeeringsAsJSON;
function displayPeerings(space, peerings) {
    heroku_cli_util_1.hux.styledHeader(`${space} Peerings`);
    heroku_cli_util_1.hux.table(peerings, {
        pcx_id: {
            header: 'PCX ID',
        },
        type: {
            header: 'Type',
        },
        cidr_blocks: {
            header: 'CIDR Blocks',
            get: (row) => (0, format_1.displayCIDR)(row.cidr_blocks),
        },
        status: {
            header: 'Status',
            get: (row) => (0, format_1.peeringStatus)(row.status),
        },
        aws_vpc_id: {
            header: 'VPC ID',
        },
        aws_region: {
            header: 'AWS Region',
        },
        aws_account_id: {
            header: 'AWS Account ID',
        },
        expires: {
            header: 'Expires',
        },
    });
}
exports.displayPeerings = displayPeerings;
