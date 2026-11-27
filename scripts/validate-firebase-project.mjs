import fs from "node:fs";
import path from "node:path";

const repoRoot = process.cwd();
const firebaseRoot = path.join(repoRoot, "firebase");
const configPath = path.join(firebaseRoot, "firebase.json");
const aliasPath = path.join(firebaseRoot, ".firebaserc");
const rulesPath = path.join(firebaseRoot, "database.rules.json");

function readJson(filePath, label) {
  if (!fs.existsSync(filePath)) throw new Error(label + " não encontrado: " + path.relative(repoRoot, filePath));
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch (error) {
    throw new Error(label + " contém JSON inválido: " + error.message);
  }
}

const config = readJson(configPath, "firebase/firebase.json");
const aliases = readJson(aliasPath, "firebase/.firebaserc");
const rules = readJson(rulesPath, "firebase/database.rules.json");

const expectedProject = "ai-messenger-b97df";
if (aliases.projects?.default !== expectedProject) {
  throw new Error("Alias Firebase default precisa ser " + expectedProject);
}

const publicDir = path.resolve(firebaseRoot, config.hosting?.public ?? "");
const invitePage = path.join(publicDir, "i", "index.html");
if (!fs.existsSync(invitePage)) {
  throw new Error("Página de convite não encontrada em " + path.relative(repoRoot, invitePage));
}

const rewrite = (config.hosting?.rewrites ?? []).some(
  (item) => item.source === "/i/**" && item.destination === "/i/index.html"
);
if (!rewrite) throw new Error("Rewrite /i/** -> /i/index.html ausente.");
if (config.hosting.public !== "public") throw new Error("Hosting public deve ser public, relativo a firebase/firebase.json.");
if (!(config.hosting.ignore ?? []).includes("**/*.template")) {
  throw new Error("Arquivos de template não estão excluídos da publicação do Hosting.");
}

if (config.database?.rules !== "database.rules.json") {
  throw new Error("Realtime Database deve apontar para database.rules.json dentro de firebase/.");
}
if (!rules.rules || typeof rules.rules !== "object") {
  throw new Error("Estrutura raiz das regras do Realtime Database inválida.");
}
function findOpenPermission(node, currentPath = "rules") {
  if (!node || typeof node !== "object" || Array.isArray(node)) return null;
  for (const [key, value] of Object.entries(node)) {
    const nextPath = currentPath + "." + key;
    if ((key === ".read" || key === ".write") &&
        (value === true || (typeof value === "string" && value.trim() === "true"))) {
      return nextPath;
    }
    const nested = findOpenPermission(value, nextPath);
    if (nested) return nested;
  }
  return null;
}

const openPermissionPath = findOpenPermission(rules.rules);
if (openPermissionPath) {
  throw new Error("Regra aberta detectada em " + openPermissionPath + "; deploy bloqueado.");
}

console.log("FIREBASE_PROJECT_CONFIG_OK");
console.log("project_id=" + expectedProject);
console.log("hosting_public=" + path.relative(repoRoot, publicDir));
console.log("database_rules=" + path.relative(repoRoot, rulesPath));
console.log("invite_route=/i/{conversationId}/{token}");
