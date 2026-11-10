package org.narna.mobile.navigation

import androidx.compose.runtime.Composable
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.navArgument
import org.narna.mobile.ui.chat.ChatScreen
import org.narna.mobile.ui.main.MainTabsScreen
import org.narna.mobile.ui.pairing.PairingScreen

sealed class Screen(val route: String) {
    object Pairing : Screen("pairing")
    object Main : Screen("main")
    object Chat : Screen("chat/{botId}") {
        fun createRoute(botId: String) = "chat/$botId"
    }

    /** @deprecated Prefer [Main] tab shell after pairing. */
    object BotList : Screen("bot_list")
    object Settings : Screen("settings")
}

@Composable
fun NavGraph(
    navController: NavHostController,
    startDestination: String
) {
    NavHost(
        navController = navController,
        startDestination = startDestination
    ) {
        composable(Screen.Pairing.route) {
            PairingScreen(
                onPaired = {
                    navController.navigate(Screen.Main.route) {
                        popUpTo(Screen.Pairing.route) { inclusive = true }
                    }
                }
            )
        }

        composable(Screen.Main.route) {
            MainTabsScreen(
                onBotClick = { botId ->
                    navController.navigate(Screen.Chat.createRoute(botId))
                },
                onUnpaired = {
                    navController.navigate(Screen.Pairing.route) {
                        popUpTo(0) { inclusive = true }
                    }
                }
            )
        }

        composable(
            route = Screen.Chat.route,
            arguments = listOf(
                navArgument("botId") { type = NavType.StringType }
            )
        ) {
            ChatScreen(
                botId = it.arguments?.getString("botId") ?: "",
                onNavigateBack = {
                    navController.popBackStack()
                }
            )
        }
    }
}
