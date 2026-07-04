FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Exponer el puerto de Vite
EXPOSE 5173

# Comando para iniciar en modo desarrollo
CMD ["npm", "run", "dev", "--", "--host"]
