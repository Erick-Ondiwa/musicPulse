/** Centralized HTTP client for every FastAPI endpoint used by the React app. */
import axios from "axios";

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 65_000,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      "The request failed.";

    return Promise.reject(new Error(message));
  },
);

export const musicApi = {
  latestSongs: async ({ limit = 10, hours } = {}) =>
    (
      await api.get("/songs/latest", {
        params: {
          limit,
          ...(hours ? { hours } : {}),
        },
      })
    ).data,

  trendingSongs: async ({ limit = 10, lookbackHours = 24 } = {}) =>
    (
      await api.get("/songs/trending", {
        params: {
          limit,
          lookback_hours: lookbackHours,
        },
      })
    ).data,

  mostViewedSongs: async ({ limit = 10, publishedWithinHours } = {}) =>
    (
      await api.get("/songs/most-viewed", {
        params: {
          limit,
          ...(publishedWithinHours
            ? {
                published_within_hours: publishedWithinHours,
              }
            : {}),
        },
      })
    ).data,

  /**
   * Retrieve the most popular videos currently stored in the database.
   *
   * This should normally be called after ingestPopular() so that the
   * returned results reflect the latest YouTube collection.
   */
  getPopularVideos: async ({
    limit = 10,
    publishedWithinHours,
  } = {}) =>
    (
      await api.get("/songs/most-viewed", {
        params: {
          limit,
          ...(publishedWithinHours
            ? {
                published_within_hours: publishedWithinHours,
              }
            : {}),
        },
      })
    ).data,

  topArtists: async ({ limit = 10 } = {}) =>
    (
      await api.get("/artists/top", {
        params: {
          limit,
        },
      })
    ).data,

  // AI requests may include local model loading, retrieval and Gemini.
  askAssistant: async ({ question, conversationId }) =>
    (
      await api.post(
        "/assistant/ask",
        {
          question,
          conversation_id: conversationId || null,
        },
        {
          timeout: 300_000,
        },
      )
    ).data,

  listConversations: async () =>
    (await api.get("/assistant/conversations")).data,

  getConversation: async (id) =>
    (await api.get(`/assistant/conversations/${id}`)).data,

  listKnowledge: async () =>
    (await api.get("/knowledge/documents")).data,

  // Re-embedding many videos can take several minutes on CPU.
  syncKnowledge: async () =>
    (
      await api.post("/knowledge/sync-videos", null, {
        timeout: 600_000,
      })
    ).data,

  addKnowledge: async (payload) =>
    (
      await api.post("/knowledge/documents", payload, {
        timeout: 300_000,
      })
    ).data,

  /**
   * Fetch YouTube's current popular music videos and insert or update
   * them in the database.
   */
  ingestPopular: async ({
    regionCode = "KE",
    maxResults = 25,
  } = {}) =>
    (
      await api.post("/ingestion/popular", null, {
        params: {
          region_code: regionCode,
          max_results: maxResults,
        },
        timeout: 300_000,
      })
    ).data,

  /**
   * Discover recently published music videos and store them in the database.
   */
  ingestRecent: async ({
    regionCode = "KE",
    hours = 24,
    maxResults = 25,
  } = {}) =>
    (
      await api.post("/ingestion/recent", null, {
        params: {
          region_code: regionCode,
          hours,
          max_results: maxResults,
        },
        timeout: 300_000,
      })
    ).data,

  refreshStatistics: async () =>
    (
      await api.post("/ingestion/refresh-statistics", null, {
        timeout: 300_000,
      })
    ).data,
};