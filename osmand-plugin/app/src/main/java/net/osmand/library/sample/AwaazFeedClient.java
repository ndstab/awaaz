package net.osmand.library.sample;

import android.util.Xml;

import org.xmlpull.v1.XmlPullParser;

import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.ArrayList;
import java.util.List;

public class AwaazFeedClient {

	public static class FeedIncident {
		public final String id;
		public final String type;
		public final String severity;
		public final double lat;
		public final double lon;

		public FeedIncident(String id, String type, String severity, double lat, double lon) {
			this.id = id;
			this.type = type;
			this.severity = severity;
			this.lat = lat;
			this.lon = lon;
		}
	}

	public List<FeedIncident> fetch(String feedUrl) throws Exception {
		URL url = new URL(feedUrl);
		HttpURLConnection conn = (HttpURLConnection) url.openConnection();
		conn.setConnectTimeout(8000);
		conn.setReadTimeout(8000);
		conn.setRequestMethod("GET");
		conn.setRequestProperty("Accept", "application/xml");

		int code = conn.getResponseCode();
		if (code < 200 || code >= 300) {
			throw new RuntimeException("Feed HTTP " + code);
		}

		try (InputStream is = conn.getInputStream()) {
			return parse(is);
		} finally {
			conn.disconnect();
		}
	}

	private List<FeedIncident> parse(InputStream is) throws Exception {
		XmlPullParser parser = Xml.newPullParser();
		parser.setInput(is, null);

		List<FeedIncident> out = new ArrayList<>();

		String currentId = null;
		String currentType = null;
		String currentSeverity = null;
		Double currentLat = null;
		Double currentLon = null;

		int eventType = parser.getEventType();
		while (eventType != XmlPullParser.END_DOCUMENT) {
			if (eventType == XmlPullParser.START_TAG) {
				String name = parser.getName();
				if ("incident".equals(name)) {
					currentId = parser.getAttributeValue(null, "id");
					currentType = null;
					currentSeverity = null;
					currentLat = null;
					currentLon = null;
				} else if ("type".equals(name)) {
					currentType = readText(parser);
				} else if ("severity".equals(name)) {
					currentSeverity = readText(parser);
				} else if ("polyline".equals(name)) {
					String text = readText(parser);
					double[] latLon = parseLatLon(text);
					currentLat = latLon[0];
					currentLon = latLon[1];
				}
			} else if (eventType == XmlPullParser.END_TAG) {
				if ("incident".equals(parser.getName())) {
					if (currentLat != null && currentLon != null) {
						out.add(new FeedIncident(
								currentId != null ? currentId : "",
								currentType != null ? currentType : "",
								currentSeverity != null ? currentSeverity : "",
								currentLat,
								currentLon
						));
					}
				}
			}
			eventType = parser.next();
		}

		return out;
	}

	private static String readText(XmlPullParser parser) throws Exception {
		parser.next();
		String text = parser.getText();
		parser.nextTag();
		return text != null ? text.trim() : "";
	}

	private static double[] parseLatLon(String polyline) {
		// Backend emits "lat,lng"
		String[] parts = polyline.split(",");
		if (parts.length != 2) {
			throw new IllegalArgumentException("Bad polyline: " + polyline);
		}
		double lat = Double.parseDouble(parts[0].trim());
		double lon = Double.parseDouble(parts[1].trim());
		return new double[]{lat, lon};
	}
}

