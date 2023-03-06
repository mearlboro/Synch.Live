import "@hotwired/turbo-rails"

import { Application } from "@hotwired/stimulus"

import FlashController from "./controllers/flash_controller.js"

window.Stimulus = Application.start()
Stimulus.register("flash", FlashController)
