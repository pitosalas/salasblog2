/**
 * Legacy Admin Functions
 * Provides backward compatibility for direct function calls
 */

// Legacy function aliases for any remaining direct calls
async function syncRaindrops() { 
    window.adminPanel?.runOperation('sync-btn'); 
}

async function regenerateSite() { 
    window.adminPanel?.runOperation('regen-btn'); 
}

async function syncToVolume() { 
    window.adminPanel?.runOperation('sync-to-volume-btn'); 
}

async function syncFromVolume() { 
    window.adminPanel?.runOperation('sync-from-volume-btn'); 
}

async function bidirectionalSync() { 
    window.adminPanel?.runOperation('bidirectional-sync-btn'); 
}

async function gitSyncNow() { 
    window.adminPanel?.runOperation('git-sync-now-btn'); 
}

async function raindropSyncNow() { 
    window.adminPanel?.runOperation('raindrop-sync-now-btn'); 
}

async function startScheduler() { 
    window.adminPanel?.runOperation('scheduler-start-btn'); 
}

async function stopScheduler() { 
    window.adminPanel?.runOperation('scheduler-stop-btn'); 
}

async function syncPagesFromRepo() { 
    window.adminPanel?.runOperation('sync-pages-btn'); 
}

async function emergencyRestore() { 
    window.adminPanel?.runOperation('emergency-restore-btn'); 
}