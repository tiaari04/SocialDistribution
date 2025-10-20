"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.displayVPNConfigInfo = void 0;
const heroku_cli_util_1 = require("@heroku/heroku-cli-util");
function displayVPNConfigInfo(space, name, config) {
    heroku_cli_util_1.hux.styledHeader(`${name} VPN Tunnels`);
    const configTunnels = config.tunnels || [];
    configTunnels.forEach((val, i) => {
        val.tunnel_id = 'Tunnel ' + (i + 1);
        val.routable_cidr = config.space_cidr_block;
        val.ike_version = config.ike_version;
    });
    heroku_cli_util_1.hux.table(configTunnels, {
        tunnel_id: { header: 'VPN Tunnel' },
        customer_ip: { header: 'Customer Gateway' },
        ip: { header: 'VPN Gateway' },
        pre_shared_key: { header: 'Pre-shared Key' },
        routable_cidr: { header: 'Routable Subnets' },
        ike_version: { header: 'IKE Version' },
    });
}
exports.displayVPNConfigInfo = displayVPNConfigInfo;
