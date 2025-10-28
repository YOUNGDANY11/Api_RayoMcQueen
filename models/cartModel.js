const db = require('../config/db')
const {Schema, model} = require('mongoose')


const cartSchema = new Schema({
    instruccion : {type: String, required: true},
})
module.exports = model('acciones', cartSchema)
