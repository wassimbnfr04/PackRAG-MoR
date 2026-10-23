package org.packrag.product

import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.heightIn
import androidx.compose.material3.Button
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.dp

/** Keep the actual button bounds, including multiline labels, at least 48dp high. */
@Composable fun ProductButton(onClick:()->Unit,modifier:Modifier=Modifier,enabled:Boolean=true,
    content:@Composable RowScope.()->Unit) {
    Button(onClick=onClick,modifier=modifier.heightIn(min=48.dp),enabled=enabled,content=content)
}

data class ProductUiLayout(val fontScale:Float,val maximumWidthDp:Int)

@Composable fun ProductLayoutScope(layout:ProductUiLayout?,content:@Composable ()->Unit) {
    if(layout==null) content() else {
        val density=Density(LocalDensity.current.density,layout.fontScale)
        val configuration=android.content.res.Configuration(LocalConfiguration.current).apply {
            fontScale=layout.fontScale;screenWidthDp=layout.maximumWidthDp
        }
        CompositionLocalProvider(LocalDensity provides density,LocalConfiguration provides configuration,content=content)
    }
}

/** Debug isolated-window resource tests never change global phone settings or production roots. */
fun isolatedUiLayout(allowDevelopment:Boolean,id:String?,fontScale:Float,widthDp:Int):ProductUiLayout? {
    if(!allowDevelopment || id==null) return null
    val valid=runCatching { java.util.UUID.fromString(id).toString()==id }.getOrDefault(false)
    if(!valid || fontScale !in setOf(1f,2f) || widthDp!=320) return null
    return ProductUiLayout(fontScale,widthDp)
}
