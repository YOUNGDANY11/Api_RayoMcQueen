const express = require('express')
const cors = require('cors')
const db = require('./config/db')
const cartRoutes = require('./routes/cartRoutes')

const app = express()
const PORT = process.env.PORT || 3000

// Conectar a la base de datos antes de iniciar el servidor
db()

app.use(cors())
app.use(express.json())
app.use(express.urlencoded({extended:true}))

app.use('/api', cartRoutes)
app.listen(PORT, () =>{
    console.log(`Server corriendo en el puerto ${PORT}`)
})