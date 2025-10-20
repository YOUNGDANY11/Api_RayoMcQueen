const express = require('express')
const router = express.Router()
const cartController = require('../controllers/cartController')

router.get('/instrucciones', cartController.getInstructions)
router.post('/instrucciones', cartController.createInstruction)
module.exports = router