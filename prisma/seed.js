const { PrismaClient } = require('@prisma/client');
const bcrypt = require('bcrypt');
const prisma = new PrismaClient();

async function main() {
  const hashedPassword = await bcrypt.hash('test123', 10);
  await prisma.user.upsert({
    where: { email: 'test@example.com' },
    update: {},
    create: {
      email: 'test@example.com',
      password: hashedPassword,
      balance: 1000,
    },
  });
  console.log('Seed complete');
}

main()
  .catch(e => console.error(e))
  .finally(() => prisma.$disconnect());
