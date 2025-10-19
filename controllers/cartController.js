const cartModel = require('../models/cartModel')

const getInstructions = async(req, res) =>{
    try{
        const instrucciones = await cartModel.find()
        if(instrucciones.length === 0){
            return res.status(404).json({
                status:'error',
                mensaje:'No se encontraron instrucciones'
            })
        }
        return res.status(200).json({
            status:'success',
            instrucciones
        })
    }catch(error){
        console.log(error)
        return res.status(500).json({
            status:'Error',
            mensaje:'No se pudieron obtener las instrucciones'
        })
    }
}

const getForSesions = async(req,res)=>{
    try{
        const {sesion} = req.params
        const instrucciones = await cartModel.find({sesion})
        if(instrucciones.length === 0){
            return res.status(404).json({
                status:'error',
                mensaje:'No se encontraron instrucciones para esta sesion'
            })
        }
        return res.status(200).json({
            status:'success',
            instrucciones
        })
    }catch(error){
        return res.status(500).json({
            status:'Error',
            mensaje:'No se pudieron obtener las instrucciones por esta sesion'
        })
    }
}

const createInstruction = async(req, res) =>{
    try{
        const {instruccion,velocidad} = req.body
        if(!instruccion || !velocidad){
            return res.status(400).json({
                status:'error',
                mensaje:'Faltan datos obligatorios'
            })
        }
        const nuevaInstruccion = new cartModel({instruccion,velocidad})
        await nuevaInstruccion.save()
        return res.status(201).json({
            status:'success',
            nuevaInstruccion
        })
    }catch(error){
	console.log(error)
        return res.status(500).json({
            status:'Error',
            mensaje:'No se pudo crear la instruccion'
        })
    }
}

module.exports = {
    getInstructions, 
    createInstruction,
    getForSesions
}
