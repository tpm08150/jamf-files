/* ------------------------------------------------------------------
   Page config.

   ⚠️ The FileCloud share link is NOT here, on purpose. This repo is
   public. The link lives in Firestore at eventLinks/<eventId> and is
   handed out only to a signed-in, allowlisted account — change it with
   ./tools/set-link.py, never here.

   The Firebase values below are the same public web config the Hub
   ships; they identify the project, they are not secrets, and the
   Firestore rules are what actually keeps the link private.
   ------------------------------------------------------------------ */
window.EVENT_CONFIG = {
  // Which document in eventLinks/ this page shows.
  eventId: "jamf-2026",

  // What to show before sign-in, when we don't know the event yet.
  fallbackName: "Event Files",

  firebase: {
    apiKey: "AIzaSyCeYKgrRN1yU9lNweFKpIeANPwh0virakA",
    authDomain: "hmx-pm-toolbox.firebaseapp.com",
    projectId: "hmx-pm-toolbox",
    storageBucket: "hmx-pm-toolbox.firebasestorage.app",
    messagingSenderId: "455425555316",
    appId: "1:455425555316:web:45ff77e17f84f922c70a21"
  }
};
