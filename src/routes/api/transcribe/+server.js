import { json } from '@sveltejs/kit';
import { writeFile, mkdir, unlink } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';

const UPLOAD_DIR = path.resolve('uploads');
const PYTHON_SCRIPT = path.resolve('python/transcribe.py');

/**
 * @param {string} audioPath
 * @returns {Promise<any>}
 */
async function runPython(audioPath) {
	return new Promise((resolve, reject) => {
        const PYTHON_BIN = path.resolve('.venv/bin/python');
        const py = spawn(PYTHON_BIN, [PYTHON_SCRIPT, audioPath]);


		let stdout = '';
		let stderr = '';
		console.log(audioPath)
		py.stdout.on('data', (data) => {
			stdout += data.toString();
		});

		py.stderr.on('data', (data) => {
			stderr += data.toString();
		});

		py.on('close', (code) => {
			console.log('Python exit code:', code);
			console.log('Python stdout:', stdout);
			console.log('Python stderr:', stderr);
			if (code !== 0) {
				reject(new Error(stderr || 'Python script failed'));
				return;
			}

			try {
				resolve(JSON.parse(stdout));
			} catch (error) {
				reject(new Error('Python returned invalid JSON: ' + stdout));
			}
		});
	});
}

/** @param {{ request: import('@sveltejs/kit').RequestEvent['request'] }} event */
export async function POST({ request }) {
	let savedPath = null;

	try {
		const formData = await request.formData();
		const audio = formData.get('audio');

		if (!audio || !(audio instanceof Blob)) {
			return json(
				{ error: 'No audio file received' },
				{ status: 400 }
			);
		}

		if (!existsSync(UPLOAD_DIR)) {
			await mkdir(UPLOAD_DIR, { recursive: true });
		}

		const arrayBuffer = await audio.arrayBuffer();
		const buffer = Buffer.from(arrayBuffer);

		const filename = `recording-${Date.now()}.webm`;
		savedPath = path.join(UPLOAD_DIR, filename);

		await writeFile(savedPath, buffer);

		const result = await runPython(savedPath);

		return json(result);
	} catch (error) {
		console.error(error);

		return json(
			{
				error:
					error instanceof Error
						? error.message
						: typeof error === 'string'
						? error
						: 'Transcription failed'
			},
			{ status: 500 }
		);
	} finally {
		if (savedPath) {
			try {
				//await unlink(savedPath);
			} catch {
				// Ignore cleanup errors
			}
		}
	}
}