import React from 'react'
import Lottie from 'lottie-react'
import { motion } from 'framer-motion'
import aibot from '../animations/aibot.json'
import burger from '../animations/burger.json'

export const ActivityIndicator = ({ message }) => {
  return (
    <div className="flex justify-start mb-4 animate-fadeIn">
      <div className="flex items-center">
        {/* Animated bot avatar */}
        <Lottie
          animationData={aibot}
          loop={true}
          className="w-14 h-14 flex-shrink-0"
        />

        {/* Moving food animation (WhatsApp-style typing) */}
        <motion.div
          animate={{ x: ["0%", "100%"] }}
          transition={{
            duration: 6,
            repeat: Infinity,
            ease: "linear",
          }}
          className="ml-2"
        >
          <div className="flex items-center">
            <Lottie
              animationData={burger}
              loop={true}
              className="h-28 w-28"
            />
          </div>
        </motion.div>
      </div>
    </div>
  )
}
