// UI and API use the same origin by default. Change paths here if the team API differs.
window.APP_CONFIG = {
  apiBaseUrl: '',
  requestTimeoutMs: 10000,
  endpoints: {events:'/events', vacancies:'/vacancies', loyalty:'/loyalty'},
};
