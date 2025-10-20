const express = require('express')
const cors = require('cors')
const db = require('./config/db')
const cartRoutes = require('./routes/cartRoutes')

const app = express()
const PORT = process.env.PORT || 3000

// Conectar a la base de datos antes de iniciar el servidor
db()

app.use(cors())

// Capturar el body crudo para poder inspeccionarlo en caso de error de JSON
app.use(express.json({
  verify: (req, res, buf, encoding) => {
    try {
      req.rawBody = buf && buf.toString(encoding || 'utf8')
    } catch (e) {
      req.rawBody = undefined
    }
  },
  limit: '100kb' // ajusta si esperas cuerpos más grandes
}))

app.use(express.urlencoded({extended:true}))

app.use('/api', cartRoutes)

// Manejador centralizado de errores de parsing JSON
app.use((err, req, res, next) => {
  if (err && err.type === 'entity.parse.failed') {
    console.error('Error parseando JSON en request:', err.message)
    // Log del body crudo para diagnóstico
    console.error('Raw body:', req.rawBody)
    return res.status(400).json({
      status: 'error',
      mensaje: 'JSON inválido en request body',
      detalle: err.message,
      rawBody: req.rawBody ? req.rawBody : undefined
    })
  }
  // otros errores
  console.error('Unhandled error middleware:', err && err.stack ? err.stack : err)
  next(err)
})

app.listen(PORT, () =>{
    console.log(`Server corriendo en el puerto ${PORT}`)
})