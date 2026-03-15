const fs = require('fs');
const glob = require('glob');

const files = glob.sync('d:/4o2/src/pages/*.jsx');
for (let file of files) {
  let content = fs.readFileSync(file, 'utf8');
  content = content.replace(/import Navbar from '..\/components\/layout\/Navbar';\n/g, '');
  content = content.replace(/import Navbar from '\.\/Navbar';\n/g, '');
  content = content.replace(/<Navbar \/>\n\s*/g, '');
  fs.writeFileSync(file, content);
  console.log('Cleaned', file);
}
