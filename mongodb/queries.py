import pandas as pd
from mongodb.connection import get_collection


# ---------------------------------------------------
# LOAD ALL DATA
# ---------------------------------------------------
def get_all_sessions():
    """
    Return all Wi-Fi session records as DataFrame.
    """

    collection = get_collection()

    data = list(
        collection.find(
            {},
            {"_id": 0}
        )
    )

    return pd.DataFrame(data)


# ---------------------------------------------------
# TOP HOTSPOTS
# ---------------------------------------------------
def get_top_hotspots(limit=10):

    collection = get_collection()

    pipeline = [
        {
            "$group": {
                "_id": "$node_id",
                "sessions": {
                    "$sum": 1
                }
            }
        },
        {
            "$sort": {
                "sessions": -1
            }
        },
        {
            "$limit": limit
        }
    ]

    data = list(
        collection.aggregate(pipeline)
    )

    return pd.DataFrame(data)


# ---------------------------------------------------
# UNIQUE USERS PER NODE
# ---------------------------------------------------
def get_unique_users_per_node():

    collection = get_collection()

    pipeline = [
        {
            "$group": {
                "_id": "$node_id",
                "users": {
                    "$addToSet":
                    "$mac_address_hashed"
                }
            }
        },
        {
            "$project": {
                "node_id": "$_id",
                "unique_users": {
                    "$size": "$users"
                }
            }
        }
    ]

    data = list(
        collection.aggregate(pipeline)
    )

    return pd.DataFrame(data)


# ---------------------------------------------------
# CROWD DENSITY
# ---------------------------------------------------
def get_crowd_density():

    collection = get_collection()

    pipeline = [
        {
            "$addFields": {
                "hour_window": {
                    "$dateToString": {
                        "format":
                        "%Y-%m-%d %H:00",
                        "date": {
                            "$toDate":
                            "$timestamp"
                        }
                    }
                }
            }
        },
        {
            "$group": {
                "_id": {
                    "node_id":
                    "$node_id",

                    "hour":
                    "$hour_window"
                },

                "users": {
                    "$addToSet":
                    "$mac_address_hashed"
                },

                "sessions": {
                    "$sum": 1
                },

                "bytes": {
                    "$sum":
                    "$bytes_transferred"
                }
            }
        },
        {
            "$project": {
                "_id": 0,

                "node_id":
                "$_id.node_id",

                "hour":
                "$_id.hour",

                "crowd_density": {
                    "$size":
                    "$users"
                },

                "sessions": 1,

                "bytes": 1
            }
        }
    ]

    data = list(
        collection.aggregate(pipeline)
    )

    return pd.DataFrame(data)


# ---------------------------------------------------
# NODE STATISTICS
# ---------------------------------------------------
def get_node_statistics():

    collection = get_collection()

    pipeline = [
        {
            "$group": {
                "_id": "$node_id",

                "sessions": {
                    "$sum": 1
                },

                "users": {
                    "$addToSet":
                    "$mac_address_hashed"
                },

                "total_bytes": {
                    "$sum":
                    "$bytes_transferred"
                },

                "avg_duration": {
                    "$avg":
                    "$connection_duration_secs"
                }
            }
        },
        {
            "$project": {
                "_id": 0,

                "node_id":
                "$_id",

                "sessions": 1,

                "unique_users": {
                    "$size":
                    "$users"
                },

                "total_bytes": 1,

                "avg_duration": {
                    "$round":
                    ["$avg_duration", 2]
                }
            }
        }
    ]

    data = list(
        collection.aggregate(pipeline)
    )

    return pd.DataFrame(data)


# ---------------------------------------------------
# MAP DATA
# ---------------------------------------------------
def get_map_data():

    collection = get_collection()

    pipeline = [
        {
            "$group": {
                "_id": {
                    "node_id":
                    "$node_id",

                    "lat":
                    "$coordinates_lat",

                    "lon":
                    "$coordinates_lon"
                },

                "sessions": {
                    "$sum": 1
                },

                "users": {
                    "$addToSet":
                    "$mac_address_hashed"
                }
            }
        },
        {
            "$project": {
                "_id": 0,

                "node_id":
                "$_id.node_id",

                "coordinates_lat":
                "$_id.lat",

                "coordinates_lon":
                "$_id.lon",

                "sessions": 1,

                "unique_users": {
                    "$size":
                    "$users"
                }
            }
        }
    ]

    data = list(
        collection.aggregate(pipeline)
    )

    return pd.DataFrame(data)


# ---------------------------------------------------
# PEAK HOURS
# ---------------------------------------------------
def get_peak_hours():

    collection = get_collection()

    pipeline = [
        {
            "$addFields": {
                "hour": {
                    "$hour": {
                        "$toDate":
                        "$timestamp"
                    }
                }
            }
        },
        {
            "$group": {
                "_id": "$hour",

                "connections": {
                    "$sum": 1
                }
            }
        },
        {
            "$sort": {
                "_id": 1
            }
        }
    ]

    data = list(
        collection.aggregate(pipeline)
    )

    return pd.DataFrame(data)
