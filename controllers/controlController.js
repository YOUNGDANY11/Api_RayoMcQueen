const controlModel = require('../models/controlModel')




const getControl = async(req, res) =>{
    try{
        const accion = await controlModel.find()
        if(accion.length === 0){
            return res.status(404).json({
                status:'error',
                mensaje:'No se encontraron accion'
            })
        }
        return res.status(200).json({
            status:'success',
            accion
        })
    }catch(error){
        console.log(error)
        return res.status(500).json({
            status:'Error',
            mensaje:'No se pudieron obtener las accion'
        })
    }
}


const createAccion = async(req, res) =>{
    try{
        const {accion} = req.body
        if(!accion ){
            return res.status(400).json({
                status:'error',
                mensaje:'Faltan datos obligatorios'
            })
        }
        const nuevaAccion = new controlModel({accion})
        await nuevaAccion.save()
        return res.status(201).json({
            status:'success',
            nuevaAccion
        })
    }catch(error){
    console.log(error)
        return res.status(500).json({
            status:'Error',
            mensaje:'No se pudo crear la accion'
        })
    }
}


module.exports = {
    getControl, 
    createAccion
}
