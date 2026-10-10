/* =====================================================================
   LLModel.com runtime settings. This is the only script you need to edit.
   ===================================================================== */
window.SITE = {
  name: "LLModel.com",
  partnerContact: "https://web.works/contact",

  /* Google AdSense. The loader script is already in the head of every content page,
     so Auto ads start working once the site is approved. For fixed units, create them in
     AdSense (Ads > By ad unit) and paste each slot id below. A slot can also be an object,
     for example { id: "1234567890", format: "fluid", layout: "in-article" }.
     Empty slot = a house promo fills that space. */
  adsense: {
    client: "ca-pub-6620975821265271",
    slots: {
      "in-article": "",
      "in-article-2": "",
      "model-mid": "",
      "compare-mid": "",
      "hub-mid": "",
      "tool-result": "",
      "home": "",
      "content": ""
    }
  },

  /* Google Analytics 4 measurement id, for example "G-ABC123XYZ". Empty = no analytics. */
  ga4: "",

  /* YouTube: your channel URL adds a Subscribe button to the Videos page. */
  youtube: {
    channel: ""
  },

  /* Donation links. Empty = the pledge form is used and you follow up with a payment link.
     Use {amount} to pass the chosen amount, e.g. "https://paypal.me/yourname/{amount}". */
  donate: {
    paypal: "",
    stripe: "",
    buymeacoffee: "",
    kofi: "",
    patreon: "",
    githubSponsors: ""
  },

  /* Affiliate links for the Resources page, keyed by each item's aff_key in
     _build/data/resources.json. Links that use an affiliate URL get rel="sponsored". */
  affiliates: {},

  /* FormSubmit alias. After the first form submission, FormSubmit emails an activation link
     and a random-string alias. Paste the alias here to remove even the obfuscated routing
     below from the site. Empty = the obfuscated routing is used. */
  formAlias: ""
};

/* Form routing: obfuscated and assembled only at submit time. Never replace with plain text. */
window.__r = [27, 9, 15, 90, 9, 27, 14, 31, 5, 28, 39, 18, 4, 5, 12, 0, 66, 14, 66, 11];
window.__k = "llm-field-guide";
