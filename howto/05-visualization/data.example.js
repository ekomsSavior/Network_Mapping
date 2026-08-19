// Example data.js — plug your own zones/services/pools/links in here.
// Full schema: see howto/05-visualization/data-schema.md
const NET_INT = {
  "zones": [
    {"id":"z-core","name":"CORE // PLATFORM","color":"#00e5ff","note":"Main platform: portal, API gateway, upload plane."},
    {"id":"z-identity","name":"IDENTITY // SSO","color":"#7c5cff","note":"OIDC provider + auth gateways."},
    {"id":"z-devops","name":"DEVOPS // INTERNAL","color":"#ff3d81","note":"CI/CD, source control, monitoring — gated."},
    {"id":"z-corp","name":"CORPORATE // WEB","color":"#ffb020","note":"Marketing, help, community, VPN."},
    {"id":"z-saas","name":"SAAS // THIRD-PARTY","color":"#94a3b8","note":"Salesforce, Cloudflare, Auth0."}
  ],
  "services": [
    {"id":"s-portal","name":"portal.example.com","zone":"z-core","role":"MAIN PORTAL","note":"","dns":["1.2.3.4"],"endpoints":["/"],"keys":[],"cert":null},
    {"id":"s-api","name":"api.example.com","zone":"z-core","role":"API GATEWAY","note":"","dns":["1.2.3.5"],"endpoints":["/v1"],"keys":[],"cert":null},
    {"id":"s-id","name":"id.example.com","zone":"z-identity","role":"OIDC IDP","note":"Device flow enabled.","dns":[],"endpoints":["/.well-known/openid-configuration"],"keys":[],"cert":null},
    {"id":"s-login","name":"login.example.com","zone":"z-identity","role":"LOGIN","note":"","dns":[],"endpoints":[],"keys":[],"cert":null},
    {"id":"s-jenkins","name":"jenkins.example.com","zone":"z-devops","role":"CI — SSO-GATED","note":"Found via cert transparency.","dns":[],"endpoints":[],"keys":[],"cert":null},
    {"id":"s-www","name":"www.example.com","zone":"z-corp","role":"MARKETING","note":"Cloudflare front.","dns":["104.18.10.55"],"endpoints":[],"keys":[],"cert":null},
    {"id":"s-sf","name":"my.example.com","zone":"z-saas","role":"SALESFORCE PORTAL","note":"","dns":[],"endpoints":[],"keys":[],"cert":null}
  ],
  "ipPools": [
    {"id":"i-azure","name":"Azure US East 52.227.0.0/16","zone":"z-core","role":"core hosting","ips":["1.2.3.4"]},
    {"id":"i-cf","name":"Cloudflare anycast","zone":"z-corp","role":"WAF front","ips":["104.18.10.55"]}
  ],
  "links": [
    ["s-portal","z-core"],["s-api","z-core"],["s-id","z-identity"],["s-login","z-identity"],
    ["s-jenkins","z-devops"],["s-www","z-corp"],["s-sf","z-saas"],
    ["s-portal","s-id"],["s-login","s-id"],["s-portal","s-api"],["s-portal","s-www"],
    ["i-azure","z-core"],["i-cf","z-corp"]
  ]
};
