const express = require('express')
const router = express.Router()
const controlController = require('../controllers/controlController')

router.get('/accion', controlController.getControl)
router.post('/accion', controlController.createAccion)
module.exports = router