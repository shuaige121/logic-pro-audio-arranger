import { spawnSync } from 'node:child_process';
import { build } from 'vite';

const tscResult = spawnSync(
  process.execPath,
  ['./node_modules/typescript/bin/tsc', '-b'],
  { stdio: 'inherit' },
);

if (tscResult.status !== 0) {
  process.exit(tscResult.status ?? 1);
}

try {
  await build();
} catch (error) {
  console.error(error);
  process.exit(1);
}
