const functions = require("firebase-functions/v1");
const logger = require("firebase-functions/logger");
const {createClient} = require("@supabase/supabase-js");
const admin = require("firebase-admin");

// Initialize Firebase Admin (only if not already initialized)
if (!admin.apps.length) {
  admin.initializeApp();
}

exports.createUserInSupabase = functions.auth.user().onCreate(async (user) => {
  // Extract user information
  const uid = user.uid;
  const displayName = user.displayName || null;
  const email = user.email || null;
  const photoURL = user.photoURL || null;

  logger.info("New user created", {uid, email, displayName});

  // Supabase operation
  try {
    // Get Supabase credentials from environment variables (Firebase secrets)
    const supabaseUrl = process.env.SUPABASE_URL;
    const supabaseKey = process.env.SUPABASE_SERVICE_KEY;

    if (!supabaseUrl || !supabaseKey) {
      logger.error("Supabase credentials not configured");
      throw new Error("Supabase credentials not configured");
    }

    // Initialize Supabase client
    const supabase = createClient(supabaseUrl, supabaseKey);

    // Insert user into Supabase users table
    const {data, error} = await supabase
        .from("users")
        .insert([
          {
            id: uid, // Using Firebase UID as primary key
            display_name: displayName,
            email: email,
            photo_url: photoURL,
          },
        ]);

    if (error) {
      logger.error("Error creating user in Supabase", {error, uid});
      throw error;
    }

    logger.info("User successfully created in Supabase", {uid, data});
  } catch (error) {
    logger.error("Failed to create user in Supabase", {error, uid});
    throw error;
  }

  // Custom claims operation
  try {
    // Set custom claim on the user's token
    await admin.auth().setCustomUserClaims(uid, {
      role: "authenticated",
    });

    logger.info("Custom claim set successfully", {uid, role: "authenticated"});
  } catch (error) {
    logger.error("Failed to set custom claims", {error, uid});
    throw error;
  }

  return {success: true, uid};
});
