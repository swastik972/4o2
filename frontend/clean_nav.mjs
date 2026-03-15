import fs from 'fs';
import { globSync } from 'glob';

const files = globSync('d:/4o2/src/pages/*.jsx');
for (let file of files) {
  let content = fs.readFileSync(file, 'utf8');
  content = content.replace(/import Navbar from '[^']+Navbar';\n?/g, '');
  content = content.replace(/<Navbar \/>\n\s*/g, '');
  fs.writeFileSync(file, content);
  console.log('Cleaned', file);
}
