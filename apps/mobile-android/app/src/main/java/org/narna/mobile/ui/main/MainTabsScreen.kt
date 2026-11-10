package org.narna.mobile.ui.main

import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Forum
import androidx.compose.material.icons.filled.Inbox
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.Schedule
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.outlined.Forum
import androidx.compose.material.icons.outlined.Inbox
import androidx.compose.material.icons.outlined.Mic
import androidx.compose.material.icons.outlined.Schedule
import androidx.compose.material.icons.outlined.Settings
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import org.narna.mobile.ui.bots.BotListScreen
import org.narna.mobile.ui.inbox.InboxScreen
import org.narna.mobile.ui.routines.RoutinesScreen
import org.narna.mobile.ui.settings.SettingsScreen
import org.narna.mobile.ui.voice.VoiceScreen

sealed class MainTab(
    val route: String,
    val label: String,
    val selectedIcon: ImageVector,
    val unselectedIcon: ImageVector
) {
    data object Bots : MainTab("tab_bots", "Bots", Icons.Filled.Forum, Icons.Outlined.Forum)
    data object Inbox : MainTab("tab_inbox", "Inbox", Icons.Filled.Inbox, Icons.Outlined.Inbox)
    data object Routines : MainTab("tab_routines", "Routines", Icons.Filled.Schedule, Icons.Outlined.Schedule)
    data object Voice : MainTab("tab_voice", "Voice", Icons.Filled.Mic, Icons.Outlined.Mic)
    data object Settings : MainTab("tab_settings", "Settings", Icons.Filled.Settings, Icons.Outlined.Settings)

    companion object {
        val all = listOf(Bots, Inbox, Routines, Voice, Settings)
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainTabsScreen(
    onBotClick: (String) -> Unit,
    onUnpaired: () -> Unit,
    viewModel: MainTabsViewModel = hiltViewModel()
) {
    val tabNavController = rememberNavController()
    val pendingCount by viewModel.pendingCount.collectAsStateWithLifecycle()

    LaunchedEffect(Unit) {
        viewModel.refreshInboxBadge()
    }

    Scaffold(
        bottomBar = {
            MainNavigationBar(
                navController = tabNavController,
                inboxBadge = pendingCount
            )
        }
    ) { paddingValues ->
        NavHost(
            navController = tabNavController,
            startDestination = MainTab.Bots.route,
            modifier = Modifier.padding(paddingValues)
        ) {
            composable(MainTab.Bots.route) {
                BotListScreen(
                    onBotClick = onBotClick,
                    showSettingsAction = false
                )
            }
            composable(MainTab.Inbox.route) {
                InboxScreen()
            }
            composable(MainTab.Routines.route) {
                RoutinesScreen()
            }
            composable(MainTab.Voice.route) {
                VoiceScreen()
            }
            composable(MainTab.Settings.route) {
                SettingsScreen(onUnpaired = onUnpaired)
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun MainNavigationBar(
    navController: NavHostController,
    inboxBadge: Int
) {
    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val currentDestination = navBackStackEntry?.destination

    NavigationBar {
        MainTab.all.forEach { tab ->
            val selected = currentDestination?.hierarchy?.any { it.route == tab.route } == true
            NavigationBarItem(
                selected = selected,
                onClick = {
                    navController.navigate(tab.route) {
                        popUpTo(navController.graph.findStartDestination().id) {
                            saveState = true
                        }
                        launchSingleTop = true
                        restoreState = true
                    }
                },
                icon = {
                    if (tab == MainTab.Inbox && inboxBadge > 0) {
                        BadgedBox(
                            badge = {
                                Badge { Text(if (inboxBadge > 99) "99+" else inboxBadge.toString()) }
                            }
                        ) {
                            Icon(
                                imageVector = if (selected) tab.selectedIcon else tab.unselectedIcon,
                                contentDescription = tab.label
                            )
                        }
                    } else {
                        Icon(
                            imageVector = if (selected) tab.selectedIcon else tab.unselectedIcon,
                            contentDescription = tab.label
                        )
                    }
                },
                label = { Text(tab.label) }
            )
        }
    }
}
