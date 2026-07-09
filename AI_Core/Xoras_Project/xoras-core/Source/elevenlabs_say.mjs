import { ElevenLabsClient, play } from '@elevenlabs/elevenlabs-js';
import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
dotenv.config({ path: path.join(__dirname, '..', '.env') });

const text = process.argv.slice(2).join(' ');
if (!text) process.exit(0);

if (!process.env.ELEVENLABS_API_KEY) {
    console.error("ELEVENLABS_API_KEY not found in .env. Falling back to native macOS say.");
    process.exit(1);
}

const elevenlabs = new ElevenLabsClient({
    apiKey: process.env.ELEVENLABS_API_KEY,
});

try {
    const audio = await elevenlabs.textToSpeech.convert(
      'JBFqnCBsd6RMkjVDRZzb', // Voice ID
      {
        text: text,
        model_id: 'eleven_multilingual_v2',
        output_format: 'mp3_44100_128',
      }
    );
    await play(audio);
} catch (error) {
    console.error("ElevenLabs Error:", error.message);
    process.exit(1);
}
