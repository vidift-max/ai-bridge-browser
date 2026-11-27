const provider = process.env.FIREBASE_WORKLOAD_IDENTITY_PROVIDER ?? "";
const serviceAccount = process.env.FIREBASE_DEPLOY_SERVICE_ACCOUNT ?? "";

const providerPattern = /^projects\/\d+\/locations\/global\/workloadIdentityPools\/[a-z0-9-]+\/providers\/[a-z0-9-]+$/;
const serviceAccountPattern = /^[a-z][a-z0-9-]*@[a-z0-9-]+\.iam\.gserviceaccount\.com$/;

const errors = [];
if (!provider) errors.push("FIREBASE_WORKLOAD_IDENTITY_PROVIDER is missing.");
else if (!providerPattern.test(provider)) errors.push("FIREBASE_WORKLOAD_IDENTITY_PROVIDER has an invalid resource-name format.");
if (!serviceAccount) errors.push("FIREBASE_DEPLOY_SERVICE_ACCOUNT is missing.");
else if (!serviceAccountPattern.test(serviceAccount)) errors.push("FIREBASE_DEPLOY_SERVICE_ACCOUNT has an invalid service-account email format.");

if (errors.length) {
  for (const error of errors) console.error("::error::" + error);
  process.exit(1);
}

console.log("FIREBASE_WIF_CONFIGURATION_SHAPE_OK");
