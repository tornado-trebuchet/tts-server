# tts-server
Text to speech local server

# API documentation 

The table below describes the available API endpoints, the expected request body, the response schema (or response type), and important notes.

| Path | Request Body | Response | Notes |
|------|--------------|----------|-------|
| `POST /tts/synthesize` | JSON: `SynthesizeRequest` { `text` (string, required), `voice_id` (UUID|null), `language` (string, default: "en"), `speed` (float, 0.5–2.0) } | Binary WAV file in response body (`Content-Type: audio/wav`). Response headers: `X-Audio-Duration` (seconds, float), `X-Sample-Rate` (Hz, int). | Generates full WAV audio and returns it as binary. OpenAPI declares binary response. Metadata is provided via headers. |
| `POST /tts/synthesize/stream` | JSON: `SynthesizeRequest` (same as above) | Streaming WAV (`Content-Type: audio/wav`) — streamed binary chunks. | Streams audio chunks; the first chunk includes the standard WAV header (so sample-rate is available in-stream). No `X-Audio-Duration` header is provided. |
| `GET /tts/voices` | None | JSON: `VoicesResponse` { `voices`: [string] } | Returns available built-in voices exposed by the TTS adapter. |
| `GET /tts/languages` | None | JSON: `LanguagesResponse` { `languages`: [string] } | Supported language codes from the TTS adapter. |
| `POST /voices/clone` | `multipart/form-data`: `name` (form string, required), `audio_files` (one or more uploaded audio files), `description` (form string, optional), `language` (form string, optional) | JSON: `VoiceResponse` { `id` (UUID), `name` (string), `description` (string), `language` (string), `created_at` (datetime), `metadata` (object) } — status `201 Created` | Creates and persists a cloned voice from uploaded samples. Returns the created voice record. |
| `GET /voices` | None | JSON: `VoiceListResponse` { `voices`: [VoiceResponse], `count`: int } | Lists cloned voices stored in the repository. |
| `GET /voices/{voice_id}` | None (path param: `voice_id` UUID) | JSON: `VoiceResponse` | Returns the cloned voice by ID. `404 Not Found` if missing. |
| `DELETE /voices/{voice_id}` | None (path param: `voice_id` UUID) | JSON: `DeleteVoiceResponse` { `success`: bool, `message`: string } | Deletes the cloned voice. `404 Not Found` if missing. |
| `POST /audio/play-bytes` | JSON: `PlayAudioRequest` { `audio_data` (bytes, required), `sample_rate` (int, default: 22050), `channels` (int, default: 1) } | JSON: `PlaybackStatusResponse` { `is_playing`: bool, `duration_seconds`: float|null } | Plays raw 16-bit PCM audio through host speakers. Blocks until complete. |
| `POST /audio/play-file` | JSON: `PlayFileRequest` { `file_path` (string, required) } | JSON: `PlaybackStatusResponse` | Plays WAV file from absolute path. `400` if invalid path/extension, `404` if not found. |
| `POST /audio/stop` | None | JSON: `PlaybackStatusResponse` | Stops current playback immediately. |
| `GET /audio/status` | None | JSON: `PlaybackStatusResponse` | Returns current playback status. |
| `GET /health` | None | JSON: `HealthResponse` { `status`: string, `version`: string } | Simple health check. |


# Notes 
Default port: 1644