const db = require('../config/db')
const {Schema, model} = require('mongoose')


const controlSchema = new Schema({
    accion : {type: String, required: true},
})
module.exports = model('accion', controlSchema)
