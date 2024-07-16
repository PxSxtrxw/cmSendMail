const http = require('http');
const nodemailer = require('nodemailer');
const { infoLogger, errorLogger } = require('./logger'); 

const transporter = nodemailer.createTransport({
    host: 'aqui va el host deseado',
    port: "tu puerto",
    secure: true,
    auth: {
        user: 'correodestinatario@ejem.com',
        pass: 'contraseña'
    },
    tls: {
        rejectUnauthorized: false
    },
    logger: true,
    debug: true
});

const server = http.createServer((req, res) => {
    let body = '';
    req.on('data', chunk => {
        body += chunk.toString(); 
    });

    req.on('end', () => {
        try {
            const jsonData = JSON.parse(body); 

            const mailOptions = {
                from: 'correodestinatario@ejem.com',
                to: jsonData.to,
                cc: jsonData.cc,
                bcc: jsonData.bcc,
                subject: jsonData.subject,
                text: jsonData.text,
            };

            // Enviar el correo
            transporter.sendMail(mailOptions, (error, info) => {
                if (error) {
                    const errorMessage = `Error al enviar el correo a ${mailOptions.to}: ${error.message}`;
                    errorLogger.error(errorMessage);
                    res.writeHead(500, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({ error: 'Error al enviar el correo' }));
                } else {
                    const successMessage = `Correo enviado correctamente a ${mailOptions.to}. Respuesta: ${info.response}`;
                    infoLogger.info(successMessage);
                    res.writeHead(200, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({ message: 'Correo enviado correctamente' }));
                }
            });

        } catch (error) {
            const parseErrorMessage = `Error al procesar la solicitud JSON: ${error.message}`;
            errorLogger.error(parseErrorMessage);
            res.writeHead(400, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: 'Error en la solicitud JSON' }));
        }
    });
});

const PORT = process.env.PORT || 4000;
server.listen(PORT, () => {
    infoLogger.info(`Servidor HTTP escuchando en el puerto ${PORT}`);
});
