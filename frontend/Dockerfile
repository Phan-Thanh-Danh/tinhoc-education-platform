FROM node:22-alpine

WORKDIR /app

# Cài đặt dependencies
COPY package*.json ./
RUN npm install

# Sao chép mã nguồn frontend
COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev"]

