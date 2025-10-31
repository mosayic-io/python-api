const functions = require("firebase-functions/v1");
const logger = require("firebase-functions/logger");
const {createClient} = require("@supabase/supabase-js");

exports.createUserInSupabase = functions.auth.user().onCreate(async (user) => {
  try {
    // Extract user information
    const uid = user.uid;
    const displayName = user.displayName || null;
    const email = user.email || null;
    const photoURL = user.photoURL || null;

    logger.info("New user created", {uid, email, displayName});

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
    return {success: true, uid};
  } catch (error) {
    logger.error("Failed to create user in Supabase", {error});
    throw error;
  }
});
