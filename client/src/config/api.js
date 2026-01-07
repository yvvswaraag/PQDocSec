export const LOCAL_API =
  import.meta.env.VITE_LOCAL_API || "http://localhost:5050";

// Peer API will be discovered dynamically
export let PEER_API = null;
export let PEER_NAME = null;
export let SELF_NAME = null;
export function setPeerApi(ip, port = 5050,name=null) {
  port =5050; //forcing port to 5050
  PEER_API = `http://${ip}:${port}`;
  PEER_NAME = name;
}
export function setSelfName(name) {
  SELF_NAME = name;
}
