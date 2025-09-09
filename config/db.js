const mongoose = require('mongoose')

const db = async() =>{
    try{
        const db= await mongoose.connect('mongodb://localhost:27017/carrito')
        console.log('Base de datos conectada a: ' + db.connection.name)
    }catch(error){
        console.log('Error al conectar a la base de datos')
        console.log(error)
    }
}

module.exports = db