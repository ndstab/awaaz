package net.osmand.library.sample;

import static net.osmand.plus.utils.InsetsUtils.InsetSide.BOTTOM;
import static net.osmand.plus.utils.InsetsUtils.InsetSide.LEFT;
import static net.osmand.plus.utils.InsetsUtils.InsetSide.RIGHT;
import static net.osmand.plus.utils.InsetsUtils.InsetSide.TOP;

import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.widget.CompoundButton;
import android.widget.Toast;

import androidx.annotation.Nullable;
import androidx.appcompat.widget.Toolbar;

import net.osmand.data.FavouritePoint;
import net.osmand.plus.OsmandApplication;
import net.osmand.plus.activities.OsmandActionBarActivity;
import net.osmand.plus.activities.RestartActivity;
import net.osmand.plus.helpers.AndroidUiHelper;
import net.osmand.plus.utils.AndroidUtils;
import net.osmand.plus.utils.InsetTarget;
import net.osmand.plus.utils.InsetTarget.InsetTargetBuilder;
import net.osmand.plus.utils.InsetsUtils;
import net.osmand.plus.views.MapViewWithLayers;
import net.osmand.plus.views.OsmandMapTileView;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class AwaazIncidentsActivity extends OsmandActionBarActivity {

	private static final long POLL_MS = 60_000;
	private static final String DEFAULT_FEED = "http://10.0.2.2:8000/feed/all/";

	private OsmandApplication app;
	private OsmandMapTileView mapTileView;
	private MapViewWithLayers mapViewWithLayers;

	private CustomPointsLayer pointsLayer;
	private final Handler handler = new Handler(Looper.getMainLooper());
	private final ExecutorService executor = Executors.newSingleThreadExecutor();
	private final AwaazFeedClient client = new AwaazFeedClient();

	@Override
	public void onCreate(@Nullable Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.simple_map_activity);
		mapViewWithLayers = findViewById(R.id.map_view_with_layers);

		app = (OsmandApplication) getApplication();
		mapTileView = app.getOsmandMap().getMapView();
		mapTileView.setupRenderingView();

		Toolbar toolbar = findViewById(R.id.toolbar);
		toolbar.setTitle("Awaaz incidents");
		toolbar.setNavigationIcon(AndroidUtils.getNavigationIconResId(app));
		toolbar.setNavigationOnClickListener(v -> onBackPressed());

		CompoundButton openglSwitch = findViewById(R.id.opengl_switch);
		openglSwitch.setChecked(app.getSettings().USE_OPENGL_RENDER.get());
		openglSwitch.setOnCheckedChangeListener((buttonView, isChecked) -> {
			app.getSettings().USE_OPENGL_RENDER.set(isChecked);
			RestartActivity.doRestart(this);
		});

		mapTileView.setIntZoom(11);
		mapTileView.setLatLon(12.9716, 77.5946);

		updateLayer(new ArrayList<>());
		schedulePoll(0);
	}

	private void schedulePoll(long delayMs) {
		handler.postDelayed(this::pollOnce, delayMs);
	}

	private void pollOnce() {
		executor.execute(() -> {
			try {
				List<AwaazFeedClient.FeedIncident> feedIncidents = client.fetch(DEFAULT_FEED);
				List<FavouritePoint> points = new ArrayList<>();
				for (AwaazFeedClient.FeedIncident inc : feedIncidents) {
					String name = inc.type + " • " + inc.severity;
					points.add(new FavouritePoint(inc.lat, inc.lon, name, "awaaz"));
				}
				runOnUiThread(() -> {
					updateLayer(points);
					Toast.makeText(this, "Awaaz: " + points.size() + " incidents", Toast.LENGTH_SHORT).show();
				});
			} catch (Exception e) {
				runOnUiThread(() -> Toast.makeText(this, "Awaaz feed error: " + e.getMessage(), Toast.LENGTH_SHORT).show());
			} finally {
				schedulePoll(POLL_MS);
			}
		});
	}

	private void updateLayer(List<FavouritePoint> points) {
		if (pointsLayer != null) {
			mapTileView.removeLayer(pointsLayer);
		}
		pointsLayer = new CustomPointsLayer(this, points);
		mapTileView.addLayer(pointsLayer, 5.5f);
		mapTileView.refreshMap();
	}

	@Override
	public void updateStatusBarColor() {
		int color = AndroidUtils.getColorFromAttr(this, android.R.attr.colorPrimary);
		if (color != -1) {
			AndroidUiHelper.setStatusBarColor(this, color);
		}
	}

	@Override
	public void onContentChanged() {
		super.onContentChanged();
		View root = findViewById(R.id.root);
		InsetTargetBuilder builder = InsetTarget.builder(root)
				.portraitSides(BOTTOM, TOP)
				.landscapeSides(TOP, RIGHT, LEFT);

		InsetsUtils.setWindowInsetsListener(root, (view, windowInsetsCompat)
				-> InsetsUtils.applyPadding(view, windowInsetsCompat, builder.build()), true);
	}

	@Override
	protected void onResume() {
		super.onResume();
		mapViewWithLayers.onResume();
	}

	@Override
	protected void onPause() {
		super.onPause();
		mapViewWithLayers.onPause();
	}

	@Override
	protected void onDestroy() {
		super.onDestroy();
		handler.removeCallbacksAndMessages(null);
		executor.shutdownNow();
		mapViewWithLayers.onDestroy();
		if (pointsLayer != null) {
			mapTileView.removeLayer(pointsLayer);
		}
	}
}

